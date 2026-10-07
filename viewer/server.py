from __future__ import annotations

import argparse
import csv
import ipaddress
import json
import re
import socket
import sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "scripts"))

from flop_strategy import cards, hand_category  # noqa: E402


ACTION_SHAPES = {
    "CHECK_DONK": ["check", "donk"],
    "CHECK_BET": ["check", "bet"],
    "FOLD_CALL_RAISE": ["fold", "call", "raise"],
    "FOLD_CALL": ["fold", "call"],
}
RANKS = "AKQJT98765432"
RANK_INDEX = {rank: index for index, rank in enumerate(RANKS)}


def combo_cell(combo: str) -> dict[str, object]:
    first, second = cards(combo)
    r1, r2 = first[0], second[0]
    if r1 == r2:
        index = RANK_INDEX[r1]
        return {"label": r1 + r2, "row": index, "col": index}
    high, low = sorted((r1, r2), key=RANK_INDEX.get)
    suited = first[1] == second[1]
    if suited:
        row, col, suffix = RANK_INDEX[high], RANK_INDEX[low], "s"
    else:
        row, col, suffix = RANK_INDEX[low], RANK_INDEX[high], "o"
    return {"label": high + low + suffix, "row": row, "col": col}


def rank_signature(text: str) -> str:
    ranks = re.findall(r"[2-9TJQKA]", text.upper())
    if len(ranks) != 3:
        return ""
    return "".join(sorted(ranks, key=RANK_INDEX.get))


def resolve_board(value: str, boards: list[str]) -> str:
    compact = re.sub(r"\s+", "", value).lower()
    for board in boards:
        if re.sub(r"\s+", "", board).lower() == compact:
            return board
    wanted = rank_signature(value)
    if wanted:
        for board in boards:
            if rank_signature(board) == wanted:
                return board
    raise ValueError(f"Flop {value!r} is not present in this study")


def select_exports(dataset_root: Path, branches: list[dict]) -> tuple[str | None, dict[str, Path]]:
    candidates: list[tuple[int, str, dict[str, Path]]] = []
    if not dataset_root.is_dir():
        return None, {}
    for run in dataset_root.iterdir():
        if not run.is_dir():
            continue
        exports = {
            branch["id"]: run / branch["id"] / "combos.csv"
            for branch in branches
            if (run / branch["id"] / "combos.csv").is_file()
        }
        if exports:
            candidates.append((len(exports), run.name, exports))
    if candidates:
        _, run_name, exports = max(candidates, key=lambda item: (item[0], item[1]))
        return run_name, exports

    # STU002 predates the shared-run layout: each branch owns its timestamped
    # run directory. Preserve support without moving or rewriting old data.
    exports = {}
    run_labels = []
    for branch in branches:
        branch_root = dataset_root / branch["id"]
        choices = sorted(branch_root.glob("*/combos.csv")) if branch_root.is_dir() else []
        if choices:
            exports[branch["id"]] = choices[-1]
            run_labels.append(choices[-1].parent.name)
    if exports:
        label = "per-branch latest / " + max(run_labels)
        return label, exports
    return None, {}


class Repository:
    def __init__(self, root: Path = REPO) -> None:
        self.root = root
        self.studies: dict[str, dict] = {}
        self._discover()

    def _discover(self) -> None:
        for study_file in sorted((self.root / "studies").glob("*/study.json")):
            with study_file.open(encoding="utf-8-sig") as handle:
                study = json.load(handle)
            slug = study_file.parent.name
            branches = study.get("branches", [])
            run_label, exports = select_exports(self.root / "datasets" / slug, branches)
            if run_label is None:
                continue
            board_path = self.root / study["board_file"]
            boards = [
                line.strip()
                for line in board_path.read_text(encoding="utf-8-sig").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            branch_by_id = {branch["id"]: branch for branch in branches}
            actor_baseline: dict[str, str] = {}
            for branch in branches:
                if branch["id"] in exports:
                    actor_baseline.setdefault(branch["acting_player"], branch["id"])
            self.studies[slug] = {
                "slug": slug,
                "study": study,
                "run_label": run_label,
                "boards": boards,
                "exports": exports,
                "branch_by_id": branch_by_id,
                "actor_baseline": actor_baseline,
            }

    def catalog(self) -> dict:
        studies = []
        for entry in self.studies.values():
            study = entry["study"]
            branches = []
            for branch in study["branches"]:
                if branch["id"] not in entry["exports"]:
                    continue
                branches.append(
                    {
                        "id": branch["id"],
                        "title": branch.get("strategy_title", branch["id"]),
                        "history": branch.get("history", ""),
                        "actionsText": branch.get("actions", ""),
                        "actor": branch["acting_player"],
                        "actions": ACTION_SHAPES[branch["action_shape"]],
                    }
                )
            studies.append(
                {
                    "slug": entry["slug"],
                    "id": study.get("study_id", entry["slug"]),
                    "name": study.get("name", entry["slug"]),
                    "rangeNote": study.get("strategy_range_note", ""),
                    "run": entry["run_label"],
                    "boards": entry["boards"],
                    "branches": branches,
                }
            )
        return {"studies": studies}

    def node(self, study_slug: str, branch_id: str, board_value: str) -> dict:
        if study_slug not in self.studies:
            raise ValueError(f"Unknown study: {study_slug}")
        entry = self.studies[study_slug]
        if branch_id not in entry["exports"]:
            raise ValueError(f"Node {branch_id!r} has no combo export")
        branch = entry["branch_by_id"][branch_id]
        board = resolve_board(board_value, entry["boards"])
        actions = ACTION_SHAPES[branch["action_shape"]]
        current_path = entry["exports"][branch_id]
        current = read_board_rows(str(current_path), board, tuple(actions))
        baseline_id = entry["actor_baseline"][branch["acting_player"]]
        baseline_branch = entry["branch_by_id"][baseline_id]
        baseline_actions = ACTION_SHAPES[baseline_branch["action_shape"]]
        baseline_path = entry["exports"][baseline_id]
        baseline_rows = read_board_rows(str(baseline_path), board, tuple(baseline_actions))
        baseline = {row["combo"]: row["reach"] for row in baseline_rows}

        result = []
        for row in current:
            base, direct, bdfd, category = hand_category(board, row["combo"])
            start_reach = baseline.get(row["combo"], row["reach"])
            reach_fraction = row["reach"] / start_reach if start_reach > 0 else 0.0
            result.append(
                {
                    **row,
                    **combo_cell(row["combo"]),
                    "baselineReach": start_reach,
                    "reachFraction": max(0.0, min(1.0, reach_fraction)),
                    "base": base,
                    "draw": direct,
                    "bdfd": bdfd,
                    "category": category,
                }
            )
        if not result:
            raise ValueError(f"No combo rows found for {board} in {branch_id}")
        return {
            "study": study_slug,
            "branch": {
                "id": branch_id,
                "title": branch.get("strategy_title", branch_id),
                "history": branch.get("history", ""),
                "actionsText": branch.get("actions", ""),
                "actor": branch["acting_player"],
            },
            "board": board,
            "boardIndex": entry["boards"].index(board) + 1,
            "actions": actions,
            "baselineBranch": baseline_id,
            "combos": result,
        }


@lru_cache(maxsize=128)
def read_board_rows(csv_name: str, board: str, actions: tuple[str, ...]) -> list[dict]:
    rows = []
    with Path(csv_name).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"board", "combo", "reach_probability"}
        required.update(f"{action}_frequency" for action in actions)
        if not required.issubset(reader.fieldnames or []):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"Missing columns in {csv_name}: {', '.join(missing)}")
        for raw in reader:
            if raw["board"] != board:
                continue
            combo = raw["combo"]
            frequencies = {action: float(raw[f"{action}_frequency"]) for action in actions}
            evs = {
                action: float(raw[f"ev_{action}"])
                for action in actions
                if raw.get(f"ev_{action}") not in (None, "")
            }
            rows.append(
                {
                    "combo": combo,
                    "cards": cards(combo),
                    "reach": float(raw["reach_probability"]),
                    "frequencies": frequencies,
                    "evs": evs,
                    "mixedEv": float(raw["mixed_ev"]) if raw.get("mixed_ev") else None,
                }
            )
    return rows


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


class ViewerHandler(BaseHTTPRequestHandler):
    repository: Repository

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/catalog":
                self.send_json(self.repository.catalog())
                return
            if parsed.path == "/api/node":
                query = parse_qs(parsed.query)
                payload = self.repository.node(
                    query.get("study", [""])[0],
                    query.get("branch", [""])[0],
                    query.get("board", [""])[0],
                )
                self.send_json(payload)
                return
            self.send_static(parsed.path)
        except (ValueError, KeyError, FileNotFoundError) as error:
            self.send_json({"error": str(error)}, status=400)
        except Exception as error:  # local diagnostic surface
            self.send_json({"error": f"Internal error: {error}"}, status=500)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path: str) -> None:
        name = "index.html" if request_path in ("", "/") else request_path.lstrip("/")
        if name not in {"index.html", "styles.css", "app.js"}:
            self.send_error(404)
            return
        path = STATIC / name
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES[path.suffix])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def private_lan_addresses() -> list[str]:
    addresses = {
        item[4][0]
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        if ipaddress.ip_address(item[4][0]).is_private
        and not ipaddress.ip_address(item[4][0]).is_loopback
    }
    return sorted(addresses)


def main() -> None:
    parser = argparse.ArgumentParser(description="Browse exported TexasSolver combo decisions")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--lan",
        action="store_true",
        help="listen on every network interface without authentication",
    )
    args = parser.parse_args()
    ViewerHandler.repository = Repository()
    if not ViewerHandler.repository.studies:
        raise SystemExit("No studies with combos.csv exports were found")
    host = args.host
    lan_addresses: list[str] = []
    if args.lan:
        lan_addresses = private_lan_addresses()
        if not lan_addresses:
            raise SystemExit("No private LAN address found; use --host with the Wi-Fi IPv4 address")
        host = "0.0.0.0"
    server = ThreadingHTTPServer((host, args.port), ViewerHandler)
    if args.lan:
        for address in lan_addresses:
            print(f"Solver visualizer: http://{address}:{args.port}")
    else:
        print(f"Solver visualizer: http://{host}:{args.port}")
    if args.lan:
        print("LAN mode has no password and listens on every interface.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "STU002__RNG001_UTG-vs-BB__BRD001_FLOP6"
DATA_ROOT = REPO / "datasets" / STUDY_ID
BOARD_FILE = REPO / "boards" / "BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt"
OUT_ROOT = DATA_ROOT / "analysis"
PURE_THRESHOLD = 0.65
EV_SCALE_PER_BB = 10.0

RANK_VALUE = {r: i for i, r in enumerate("23456789TJQKA", start=2)}
B13 = [
    "ABB", "A[K/Q]x", "A[J-T][9-5]", "A[J-T][4-2]",
    "A[9-7]x", "A[6-2]x", "BBB", "BBx",
    "K/Qx dis", "K/Qx con", "[J-8]x dis", "[J-8]x con", "[7-4]x",
]
B13_EXPECTED = dict(zip(B13, [6, 16, 10, 6, 18, 10, 4, 47, 42, 14, 67, 26, 20]))
BASE_ORDER = ["Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
              "Underpair", "Weak pair", "2 overcards", "A-high", "Air"]

BRANCHES = {
    "01_BB_FIRST": {
        "actions": ["check", "donk"], "shape": "CHECK_DONK", "actor": "BB",
        "labels": {"check": "X", "donk": "D"},
    },
    "02_UTG_AFTER_CHECK": {
        "actions": ["check", "bet"], "shape": "CHECK_BET", "actor": "UTG",
        "labels": {"check": "X", "bet": "B"},
    },
    "03_BB_AFTER_CBET": {
        "actions": ["fold", "call", "raise"], "shape": "FOLD_CALL_RAISE", "actor": "BB",
        "labels": {"fold": "F", "call": "C", "raise": "R"},
    },
    "04_UTG_AFTER_CHECK_RAISE": {
        "actions": ["fold", "call"], "shape": "FOLD_CALL", "actor": "UTG",
        "labels": {"fold": "F", "call": "C"},
    },
    "05_UTG_AFTER_DONK": {
        "actions": ["fold", "call", "raise"], "shape": "FOLD_CALL_RAISE", "actor": "UTG",
        "labels": {"fold": "F", "call": "C", "raise": "R"},
    },
    "06_BB_AFTER_DONK_RAISE": {
        "actions": ["fold", "call"], "shape": "FOLD_CALL", "actor": "BB",
        "labels": {"fold": "F", "call": "C"},
    },
}


def cards(text: str) -> list[str]:
    compact = text.replace(" ", "")
    if len(compact) not in (4, 6):
        raise ValueError(f"Unexpected card string: {text!r}")
    return [compact[i:i + 2] for i in range(0, len(compact), 2)]


def rank(card: str) -> int:
    return RANK_VALUE[card[0]]


def flop_class(board: str) -> str:
    top, mid, low = sorted((rank(c) for c in cards(board)), reverse=True)
    if top == 14:
        if mid >= 10:
            if low >= 10:
                return "ABB"
            if mid in (13, 12):
                return "A[K/Q]x"
            if 5 <= low <= 9:
                return "A[J-T][9-5]"
            return "A[J-T][4-2]"
        if 7 <= mid <= 9:
            return "A[9-7]x"
        return "A[6-2]x"
    broadway = {10, 11, 12, 13}
    if top in broadway and mid in broadway and low in broadway:
        return "BBB"
    if top in broadway and mid in broadway and low <= 9:
        if (top, mid, low) != (11, 10, 9):
            return "BBx"
    if top in (13, 12):
        return "K/Qx con" if mid - low == 1 else "K/Qx dis"
    if 8 <= top <= 11:
        return "[J-8]x con" if mid - low == 1 else "[J-8]x dis"
    return "[7-4]x"


STRAIGHTS = [{14, 2, 3, 4, 5}] + [set(range(lo, lo + 5)) for lo in range(2, 11)]


def straight_info(ranks: set[int]) -> tuple[bool, set[int]]:
    made = any(seq <= ranks for seq in STRAIGHTS)
    missing = set()
    if not made:
        for seq in STRAIGHTS:
            absent = seq - ranks
            if len(absent) == 1:
                missing.update(absent)
    return made, missing


def hand_category(board: str, combo: str) -> tuple[str, str, bool, str]:
    bc = cards(board)
    hc = cards(combo)
    board_ranks = sorted((rank(c) for c in bc), reverse=True)
    hole_ranks = [rank(c) for c in hc]
    all_ranks = board_ranks + hole_ranks
    counts = Counter(all_ranks)
    made_straight, missing = straight_info(set(all_ranks))
    pair_groups = sum(1 for n in counts.values() if n >= 2)

    if made_straight or max(counts.values()) >= 3 or pair_groups >= 2:
        base = "Two pair+"
    elif hole_ranks[0] == hole_ranks[1]:
        pr = hole_ranks[0]
        if pr > board_ranks[0]:
            base = "Overpair"
        elif board_ranks[0] > pr > board_ranks[1]:
            base = "Underpair"
        else:
            base = "Weak pair"
    elif board_ranks[0] in hole_ranks:
        base = "Top pair"
    elif board_ranks[1] in hole_ranks:
        base = "Second pair"
    elif board_ranks[2] in hole_ranks:
        base = "Third pair"
    elif all(r > board_ranks[0] for r in hole_ranks):
        base = "2 overcards"
    elif 14 in hole_ranks:
        base = "A-high"
    else:
        base = "Air"

    if made_straight:
        direct = "none"
    elif len(missing) >= 2:
        direct = "OESD"
    elif len(missing) == 1:
        direct = "Gutshot"
    else:
        direct = "none"

    hole_suits = [c[1] for c in hc]
    board_suits = {c[1] for c in bc}
    bdfd = hole_suits[0] == hole_suits[1] and hole_suits[0] in board_suits
    parts = [base]
    if direct != "none":
        parts.append(direct)
    if bdfd:
        parts.append("BDFD")
    return base, direct, bdfd, " + ".join(parts)


def hand_sort_key(label: str) -> tuple[int, int, int]:
    base = next(b for b in BASE_ORDER if label == b or label.startswith(b + " +"))
    direct = 2 if "OESD" in label else 1 if "Gutshot" in label else 0
    bdfd = 1 if label.endswith("BDFD") else 0
    return BASE_ORDER.index(base), direct, bdfd


def choose_policy(means: dict[str, float], actions: list[str]) -> tuple[str, dict[str, float]]:
    ranked = sorted(actions, key=lambda a: (-means[a], actions.index(a)))
    selected = [ranked[0]] if means[ranked[0]] > PURE_THRESHOLD else ranked[:2]
    probs = {a: 0.0 for a in actions}
    for action in selected:
        probs[action] = 1.0 / len(selected)
    return "/".join(selected), probs


def display_policy(policy: str, labels: dict[str, str]) -> str:
    selected = set(policy.split("/"))
    return "/".join(label for action, label in labels.items() if action in selected)


def latest_run(branch: str) -> Path:
    runs = sorted(p for p in (DATA_ROOT / branch).iterdir() if p.is_dir())
    if not runs:
        raise RuntimeError(f"No dataset run for {branch}")
    return runs[-1]


def validate_dataset_run(run: Path) -> dict:
    with (run / "batch-summary.json").open(encoding="utf-8-sig") as f:
        summary = json.load(f)
    done = sum(row.get("status") == "done" for row in summary)
    failed = len(summary) - done
    with (run / "validation.csv").open(encoding="utf-8-sig", newline="") as f:
        checks = list(csv.DictReader(f))
    result = {
        "boards": len(summary), "done": done, "failed": failed,
        "validation_rows": len(checks),
        "validation_pass": sum(r["result"] == "PASS" for r in checks),
        "solve_start_calls": sorted({int(r["solve_start_calls"]) for r in checks}),
        "current_street_export_calls": sorted({int(r["current_street_export_calls"]) for r in checks}),
        "forbidden_full_tree_calls": sum(int(r["forbidden_full_tree_calls"]) for r in checks),
        "combo_rows_reported": sum(int(r["combos"]) for r in checks),
    }
    required = {
        "boards": 286, "done": 286, "failed": 0, "validation_rows": 286,
        "validation_pass": 286, "solve_start_calls": [1],
        "current_street_export_calls": [1], "forbidden_full_tree_calls": 0,
    }
    for key, expected in required.items():
        if result[key] != expected:
            raise RuntimeError(f"{run}: {key}={result[key]!r}, expected {expected!r}")
    return result


def read_branch(branch: str, meta: dict) -> tuple[list[dict], dict, dict]:
    run = latest_run(branch)
    validation = validate_dataset_run(run)
    rows = []
    combo_hashes = defaultdict(list)
    csv_path = run / "combos.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        expected = ["board", "board_index", "decision_node", "acting_player", "combo",
                    "reach_probability"]
        expected += [f"{a}_frequency" for a in meta["actions"]]
        expected += [f"ev_{a}" for a in meta["actions"]] + ["mixed_ev"]
        if reader.fieldnames != expected:
            raise RuntimeError(f"{branch}: unexpected CSV header {reader.fieldnames}")
        for raw in reader:
            board = raw["board"]
            combo = raw["combo"]
            base, direct, bdfd, category = hand_category(board, combo)
            freqs = {a: float(raw[f"{a}_frequency"]) for a in meta["actions"]}
            evs = {a: float(raw[f"ev_{a}"]) for a in meta["actions"]}
            if not math.isclose(sum(freqs.values()), 1.0, abs_tol=2e-3):
                raise RuntimeError(f"{branch} {board} {combo}: frequencies do not sum to 1")
            row = {
                "board": board, "board_index": int(raw["board_index"]), "combo": combo,
                "flop_class": flop_class(board), "base": base, "direct": direct,
                "bdfd": bdfd, "hand_category": category,
                "reach": float(raw["reach_probability"]), "freqs": freqs,
                "evs": evs, "mixed_ev": float(raw["mixed_ev"]),
            }
            rows.append(row)
            combo_hashes[board].append(combo)
    if len(rows) != validation["combo_rows_reported"]:
        raise RuntimeError(f"{branch}: CSV rows {len(rows)} != reported {validation['combo_rows_reported']}")
    hashes = {board: hashlib.sha256("|".join(sorted(items)).encode()).hexdigest()
              for board, items in combo_hashes.items()}
    validation["csv_rows"] = len(rows)
    validation["zero_reach_rows"] = sum(r["reach"] <= 0 for r in rows)
    validation["classified_rows"] = len(rows)
    validation["run"] = run.name
    return rows, hashes, validation


def analyze_branch(branch: str, meta: dict, rows: list[dict]) -> dict:
    actions = meta["actions"]
    active = [r for r in rows if r["reach"] > 0]
    board_hand = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    for row in active:
        key = (row["board"], row["hand_category"])
        board_hand[key]["count"] += 1
        for action in actions:
            board_hand[key]["sums"][action] += row["freqs"][action]

    cell_means = defaultdict(lambda: {"boards": 0, "sums": defaultdict(float)})
    for (board, hand), bh in board_hand.items():
        key = (flop_class(board), hand)
        cell_means[key]["boards"] += 1
        for action in actions:
            cell_means[key]["sums"][action] += bh["sums"][action] / bh["count"]

    policies = {}
    details = {}
    for key, cell in cell_means.items():
        means = {a: cell["sums"][a] / cell["boards"] for a in actions}
        policy, probs = choose_policy(means, actions)
        policies[key] = (policy, probs)
        details[key] = {
            "flop_class": key[0], "hand_category": key[1],
            "boards_present": cell["boards"],
            **{f"mean_{a}_frequency": means[a] for a in actions},
            "policy": display_policy(policy, meta["labels"]),
            "active_combos": 0, "reach_sum": 0.0, "weighted_loss": 0.0,
            "max_combo_loss": 0.0, "frequency_distance_sum": 0.0,
        }

    branch_reach = 0.0
    branch_weighted_loss = 0.0
    solver_weighted = defaultdict(float)
    simple_weighted = defaultdict(float)
    for row in active:
        key = (row["flop_class"], row["hand_category"])
        _, probs = policies[key]
        simple_ev = sum(probs[a] * row["evs"][a] for a in actions)
        loss = max(0.0, row["mixed_ev"] - simple_ev)
        detail = details[key]
        detail["active_combos"] += 1
        detail["reach_sum"] += row["reach"]
        detail["weighted_loss"] += row["reach"] * loss
        detail["max_combo_loss"] = max(detail["max_combo_loss"], loss)
        detail["frequency_distance_sum"] += 0.5 * sum(
            abs(row["freqs"][a] - probs[a]) for a in actions)
        branch_reach += row["reach"]
        branch_weighted_loss += row["reach"] * loss
        for action in actions:
            solver_weighted[action] += row["reach"] * row["freqs"][action]
            simple_weighted[action] += row["reach"] * probs[action]

    for detail in details.values():
        detail["mean_local_loss_bb"] = (
            detail.pop("weighted_loss") / detail["reach_sum"] / EV_SCALE_PER_BB
            if detail["reach_sum"] else 0.0)
        detail["max_combo_loss_bb"] = detail.pop("max_combo_loss") / EV_SCALE_PER_BB
        detail["mean_frequency_distance"] = (
            detail.pop("frequency_distance_sum") / detail["active_combos"])

    hand_labels = sorted({r["hand_category"] for r in active}, key=hand_sort_key)
    matrix = []
    for hand in hand_labels:
        matrix.append({"hand_category": hand, **{
            fc: details.get((fc, hand), {}).get("policy", "—") for fc in B13}})

    summary = {
        "branch": branch, "acting_player": meta["actor"], "action_shape": meta["shape"],
        "threshold": PURE_THRESHOLD, "all_mixes": "strict 50/50",
        "csv_rows": len(rows), "active_rows": len(active),
        "zero_reach_rows": len(rows) - len(active), "hand_categories": len(hand_labels),
        "populated_cells": len(details),
        "mean_local_loss_bb": branch_weighted_loss / branch_reach / EV_SCALE_PER_BB,
        "reach_sum": branch_reach,
        "weighted_loss_native": branch_weighted_loss,
        "solver_reach_weighted_frequencies": {
            a: solver_weighted[a] / branch_reach for a in actions},
        "simplified_reach_weighted_frequencies": {
            a: simple_weighted[a] / branch_reach for a in actions},
        "policy_cell_counts": dict(Counter(d["policy"] for d in details.values())),
    }
    return {"matrix": matrix, "details": list(details.values()), "summary": summary}


def main() -> None:
    """Validate the tracked source datasets without creating a strategy table.

    The two supported policies are generated by
    generate-stu002-strategies.py.  Keeping this command validation-only avoids
    silently recreating superseded strict/experimental output directories.
    """
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    boards = [line.strip() for line in BOARD_FILE.read_text(encoding="utf-8-sig").splitlines()
              if line.strip() and not line.lstrip().startswith("#")]
    if len(boards) != 286 or len(set(boards)) != 286:
        raise RuntimeError(f"BRD001 expected 286 unique boards, got {len(boards)}")
    observed = Counter(flop_class(b) for b in boards)
    if dict(observed) != B13_EXPECTED:
        raise RuntimeError(f"B13 mismatch: {dict(observed)} != {B13_EXPECTED}")

    validations = {}
    hashes_by_branch = {}
    for branch, meta in BRANCHES.items():
        rows, hashes, validation = read_branch(branch, meta)
        validations[branch] = validation
        hashes_by_branch[branch] = hashes

    for group in (["01_BB_FIRST", "03_BB_AFTER_CBET", "06_BB_AFTER_DONK_RAISE"],
                  ["02_UTG_AFTER_CHECK", "04_UTG_AFTER_CHECK_RAISE", "05_UTG_AFTER_DONK"]):
        reference = hashes_by_branch[group[0]]
        for branch in group[1:]:
            if hashes_by_branch[branch] != reference:
                raise RuntimeError(f"Source combo support differs: {group[0]} vs {branch}")

    audit = {
        "board_count": len(boards),
        "b13_counts": {fc: observed[fc] for fc in B13},
        "b13_expected": B13_EXPECTED,
        "dataset_validation": validations,
        "source_combo_support_consistent": {
            "BB": ["01_BB_FIRST", "03_BB_AFTER_CBET", "06_BB_AFTER_DONK_RAISE"],
            "UTG": ["02_UTG_AFTER_CHECK", "04_UTG_AFTER_CHECK_RAISE", "05_UTG_AFTER_DONK"],
        },
        "classification": "PASS: every dataset row received exactly one base/direct/BDFD category",
    }
    with (OUT_ROOT / "SOURCE_VALIDATION.json").open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(json.dumps({"status": "PASS", "b13": audit["b13_counts"],
                      "dataset_validation": validations}, ensure_ascii=False))


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analysis = load_module("analyze_stu002", REPO / "scripts" / "analyze-stu002.py")

FINAL_ROOT = analysis.OUT_ROOT
NARROW_ROOT = FINAL_ROOT / "strategy-13"
WIDE_ROOT = FINAL_ROOT / "strategy-8"

# Display order is a learning/layout decision.  It does not alter the mutually
# exclusive base-classification priority in analyze-stu002.py.
HAND_ORDER = [
    "Two pair+",
    "Overpair",
    "Top pair",
    "Underpair",
    "Second pair",
    "Third pair",
    "Weak pair",
    "OESD",
    "Gutshot",
    "2 overcards + BDFD",
    "Air",
]

FLOP_GROUPS = [
    {
        "name": "A-high high",
        "count": 22,
        "members": ["ABB", "A[K/Q]x"],
        "short": "ABB A[K/Q]x",
        "definition": "A with two broadway cards, or A with K/Q and a lower card",
    },
    {
        "name": "A-high medium",
        "count": 16,
        "members": ["A[J-T][9-5]", "A[J-T][4-2]"],
        "short": "A[J-T]x",
        "definition": "A with J/T",
    },
    {
        "name": "A-high low",
        "count": 28,
        "members": ["A[9-7]x", "A[6-2]x"],
        "short": "A[9-2]x",
        "definition": "A with a middle card of 9 or lower",
    },
    {
        "name": "Broadway",
        "count": 51,
        "members": ["BBB", "BBx"],
        "short": "BBB BBx",
        "definition": "No A; at least two broadway cards",
    },
    {
        "name": "K/Q-high",
        "count": 56,
        "members": ["K/Qx dis", "K/Qx con"],
        "short": "K/Qx",
        "definition": "Top card K/Q, excluding BBx",
    },
    {
        "name": "Middle dry",
        "count": 67,
        "members": ["[J-8]x dis"],
        "short": "[J-8]x dis",
        "definition": "Top card J/T/9/8; lower two ranks are not adjacent",
    },
    {
        "name": "Middle connected",
        "count": 26,
        "members": ["[J-8]x con"],
        "short": "[J-8]x con",
        "definition": "Top card J/T/9/8; lower two ranks are adjacent; includes JT9",
    },
    {
        "name": "Low",
        "count": 20,
        "members": ["[7-4]x"],
        "short": "[7-4]x",
        "definition": "Top card 7 or lower",
    },
]

GROUP_BY_B13 = {
    member: group["name"] for group in FLOP_GROUPS for member in group["members"]
}


def remap_hand(row: dict) -> dict:
    """Map strict base/direct/BDFD data to the accepted 11 learnable rows.

    Made hands always keep their base.  Unmade hands use direct draw strength
    before overcards/BDFD: OESD, then Gutshot, then exactly two overcards with
    a BDFD, otherwise Air.
    """
    mapped = dict(row)
    base = row["base"]
    if base in {
        "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
        "Underpair", "Weak pair",
    }:
        label = base
    elif row["direct"] == "OESD":
        label = "OESD"
    elif row["direct"] == "Gutshot":
        label = "Gutshot"
    elif base == "2 overcards" and row["bdfd"]:
        label = "2 overcards + BDFD"
    elif base in {"2 overcards", "A-high", "Air"}:
        label = "Air"
    else:
        raise RuntimeError(f"Unsupported base category: {base}")
    mapped["hand_category"] = label
    return mapped


def aggregate(rows: list[dict], meta: dict, flop_categories: list[str],
              flop_category_for_board) -> dict:
    """Build cells from raw solver frequencies without reverse-engineering policies.

    Stage 1 is an equal mean across active concrete combos on one board and one
    displayed hand row.  Stage 2 is an equal mean across actual boards in the
    displayed flop category.  reach_probability is only a support filter here.
    """
    actions = meta["actions"]
    active = [row for row in rows if row["reach"] > 0]

    board_hand = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    for row in active:
        key = (row["board"], row["hand_category"])
        board_hand[key]["count"] += 1
        for action in actions:
            board_hand[key]["sums"][action] += row["freqs"][action]

    cells = defaultdict(lambda: {"boards": 0, "sums": defaultdict(float)})
    for (board, hand), item in board_hand.items():
        flop_category = flop_category_for_board(board)
        cell = cells[(flop_category, hand)]
        cell["boards"] += 1
        for action in actions:
            cell["sums"][action] += item["sums"][action] / item["count"]

    policies: dict[tuple[str, str], tuple[str, dict[str, float]]] = {}
    details = []
    for (flop_category, hand), item in cells.items():
        means = {action: item["sums"][action] / item["boards"] for action in actions}
        policy, probs = analysis.choose_policy(means, actions)
        policies[(flop_category, hand)] = (policy, probs)
        details.append({
            "flop_category": flop_category,
            "hand_category": hand,
            "boards_present": item["boards"],
            **{f"mean_{action}_frequency": means[action] for action in actions},
            "policy": analysis.display_policy(policy, meta["labels"]),
            "active_combos": 0,
            "reach_sum": 0.0,
            "weighted_loss_native": 0.0,
            "max_combo_loss_native": 0.0,
        })
    detail_by_key = {(d["flop_category"], d["hand_category"]): d for d in details}

    branch_reach = 0.0
    branch_loss = 0.0
    solver_weighted = defaultdict(float)
    simplified_weighted = defaultdict(float)
    for row in active:
        key = (flop_category_for_board(row["board"]), row["hand_category"])
        _, probs = policies[key]
        simple_ev = sum(probs[action] * row["evs"][action] for action in actions)
        loss = max(0.0, row["mixed_ev"] - simple_ev)
        detail = detail_by_key[key]
        detail["active_combos"] += 1
        detail["reach_sum"] += row["reach"]
        detail["weighted_loss_native"] += row["reach"] * loss
        detail["max_combo_loss_native"] = max(detail["max_combo_loss_native"], loss)
        branch_reach += row["reach"]
        branch_loss += row["reach"] * loss
        for action in actions:
            solver_weighted[action] += row["reach"] * row["freqs"][action]
            simplified_weighted[action] += row["reach"] * probs[action]

    for detail in details:
        detail["mean_local_loss_bb"] = (
            detail.pop("weighted_loss_native")
            / detail["reach_sum"]
            / analysis.EV_SCALE_PER_BB
            if detail["reach_sum"] else 0.0
        )
        detail["max_combo_loss_bb"] = (
            detail.pop("max_combo_loss_native") / analysis.EV_SCALE_PER_BB
        )

    matrix = []
    for hand in HAND_ORDER:
        row = {"hand_category": hand}
        for flop_category in flop_categories:
            detail = detail_by_key.get((flop_category, hand))
            row[flop_category] = detail["policy"] if detail else "—"
        matrix.append(row)

    summary = {
        "branch": meta.get("branch"),
        "acting_player": meta["actor"],
        "action_shape": meta["shape"],
        "threshold": analysis.PURE_THRESHOLD,
        "mix_rule": "strict 50/50 top two actions",
        "csv_rows": len(rows),
        "active_rows": len(active),
        "zero_reach_rows": len(rows) - len(active),
        "hand_categories": len(HAND_ORDER),
        "populated_cells": len(details),
        "reach_sum": branch_reach,
        "weighted_loss_native": branch_loss,
        "mean_local_loss_bb": branch_loss / branch_reach / analysis.EV_SCALE_PER_BB,
        "solver_reach_weighted_frequencies": {
            action: solver_weighted[action] / branch_reach for action in actions
        },
        "simplified_reach_weighted_frequencies": {
            action: simplified_weighted[action] / branch_reach for action in actions
        },
        "policy_cell_counts": dict(Counter(d["policy"] for d in details)),
    }
    return {"matrix": matrix, "details": details, "summary": summary}


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_model(root: Path, model: str, flop_categories: list[str], loaded: dict,
                flop_category_for_board, baseline_loss: dict | None = None) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "model": model,
        "source": "six tracked STU002 aggregate combo datasets",
        "pure_threshold": analysis.PURE_THRESHOLD,
        "mix_rule": "strict 50/50 top two actions",
        "hand_categories": HAND_ORDER,
        "flop_categories": flop_categories,
        "branches": [],
    }
    root_reach = sum(row["reach"] for row in loaded["01_BB_FIRST"] if row["reach"] > 0)
    for branch, source_rows in loaded.items():
        meta = dict(analysis.BRANCHES[branch])
        meta["branch"] = branch
        result = aggregate(source_rows, meta, flop_categories, flop_category_for_board)
        summary = result["summary"]
        summary["branch"] = branch
        summary["node_reach_fraction"] = summary["reach_sum"] / root_reach
        summary["root_loss_bb"] = (
            summary["weighted_loss_native"] / root_reach / analysis.EV_SCALE_PER_BB
        )
        if baseline_loss is not None:
            summary["incremental_root_loss_vs_B13_bb"] = (
                summary["root_loss_bb"] - baseline_loss[branch]
            )

        branch_root = root / branch
        write_csv(
            branch_root / "strategy.csv",
            result["matrix"],
            ["hand_category"] + flop_categories,
        )
        detail_fields = [
            "flop_category", "hand_category", "boards_present", "active_combos", "reach_sum",
        ] + [f"mean_{action}_frequency" for action in meta["actions"]]
        detail_fields += ["policy", "mean_local_loss_bb", "max_combo_loss_bb"]
        write_csv(branch_root / "cell-details.csv", result["details"], detail_fields)
        (branch_root / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest["branches"].append({
            "branch": branch,
            "actor": meta["actor"],
            "actions": meta["actions"],
            "labels": meta["labels"],
            "summary": summary,
        })
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def validate_board_partition() -> dict:
    boards = [
        line.strip()
        for line in analysis.BOARD_FILE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(boards) != 286 or len(set(boards)) != 286:
        raise RuntimeError(f"BRD001 expected 286 unique boards, got {len(boards)}")
    b13_counts = Counter(analysis.flop_class(board) for board in boards)
    if dict(b13_counts) != analysis.B13_EXPECTED:
        raise RuntimeError(f"B13 mismatch: {dict(b13_counts)}")
    group_counts = Counter(GROUP_BY_B13[analysis.flop_class(board)] for board in boards)
    expected = {group["name"]: group["count"] for group in FLOP_GROUPS}
    if dict(group_counts) != expected:
        raise RuntimeError(f"Eight-group mismatch: {dict(group_counts)} != {expected}")
    return {"boards": len(boards), "b13_counts": b13_counts, "group_counts": group_counts}


def main() -> None:
    partition = validate_board_partition()
    loaded = {}
    validations = {}
    hashes = {}
    for branch, meta in analysis.BRANCHES.items():
        source_rows, combo_hashes, validation = analysis.read_branch(branch, meta)
        loaded[branch] = [remap_hand(row) for row in source_rows]
        validations[branch] = validation
        hashes[branch] = combo_hashes

    for group in (
        ["01_BB_FIRST", "03_BB_AFTER_CBET", "06_BB_AFTER_DONK_RAISE"],
        ["02_UTG_AFTER_CHECK", "04_UTG_AFTER_CHECK_RAISE", "05_UTG_AFTER_DONK"],
    ):
        for branch in group[1:]:
            if hashes[branch] != hashes[group[0]]:
                raise RuntimeError(f"Combo support mismatch: {group[0]} vs {branch}")

    narrow = write_model(
        NARROW_ROOT,
        "11 hand categories x 13 B13 flop categories",
        analysis.B13,
        loaded,
        analysis.flop_class,
    )
    narrow_loss = {
        item["branch"]: item["summary"]["root_loss_bb"] for item in narrow["branches"]
    }
    wide = write_model(
        WIDE_ROOT,
        "11 hand categories x 8 flop categories",
        [group["name"] for group in FLOP_GROUPS],
        loaded,
        lambda board: GROUP_BY_B13[analysis.flop_class(board)],
        baseline_loss=narrow_loss,
    )
    audit = {
        "status": "PASS",
        "boards": partition["boards"],
        "b13_counts": {name: partition["b13_counts"][name] for name in analysis.B13},
        "eight_group_counts": {
            group["name"]: partition["group_counts"][group["name"]] for group in FLOP_GROUPS
        },
        "hand_rows": HAND_ORDER,
        "dataset_validation": validations,
        "source_combo_support_consistent": True,
        "classification": (
            "Every source combo has exactly one base category, one direct-draw state, "
            "one BDFD state, and exactly one displayed hand row."
        ),
        "frequency_source": "raw solver combo action frequencies; never reverse-derived from labels",
    }
    (FINAL_ROOT / "FINAL_VALIDATION.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (FINAL_ROOT / "FLOP_GROUPS.json").write_text(
        json.dumps(FLOP_GROUPS, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "status": "PASS",
        "narrow": NARROW_ROOT.as_posix(),
        "wide": WIDE_ROOT.as_posix(),
        "wide_mix_cells": sum(
            sum(count for policy, count in item["summary"]["policy_cell_counts"].items() if "/" in policy)
            for item in wide["branches"]
        ),
        "wide_populated_cells": sum(item["summary"]["populated_cells"] for item in wide["branches"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

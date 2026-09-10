from __future__ import annotations

import argparse
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


analysis = load_module("flop_strategy", REPO / "scripts" / "flop_strategy.py")

# Display order is a learning/layout decision.  It does not alter the mutually
# exclusive base-classification priority in flop_strategy.py.
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


def write_model(
    root: Path,
    model: str,
    source: str,
    flop_categories: list[str],
    loaded: dict,
    branch_metas: dict,
    root_reach: float,
    flop_category_for_board,
    baseline_loss: dict | None = None,
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "model": model,
        "source": source,
        "pure_threshold": analysis.PURE_THRESHOLD,
        "mix_rule": "strict 50/50 top two actions",
        "hand_categories": HAND_ORDER,
        "flop_categories": flop_categories,
        "branches": [],
    }
    for branch, source_rows in loaded.items():
        meta = branch_metas[branch]
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


def write_analysis_readme(root: Path, study: dict, study_directory: str) -> None:
    code = study["study_id"]
    text = f"""# {code} active strategy outputs

This directory contains the reproducible machine-readable strategy, validation
audits and the two human workbooks for `{study_directory}`.

Human workbooks:

- `{code}_simplified_flop_strategy.xlsx` — 11 hand rows by B13;
- `{code}_strategy_8_categories.xlsx` — the same hand rows by eight broader
  flop categories.

Machine-readable outputs:

- `strategy-13/`;
- `strategy-8/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the numeric strategy directly from the tracked solver combo frequencies:

```text
python scripts/generate-flop-strategies.py {study_directory}
```

Build the two workbooks with the approved colors and layout:

```text
node scripts/build-flop-workbooks.mjs {study_directory}
```

The full method and range provenance are in `docs/FLOP_STRATEGY_WORKFLOW.md`.
Rejected horizontal smoothing experiments remain only in Git history.
"""
    (root / "README.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build B13 and eight-category human flop strategies from solver combos."
    )
    parser.add_argument(
        "study",
        help="Study directory name below studies/ and datasets/.",
    )
    parser.add_argument(
        "--run",
        help="Exact shared run directory for layouts such as STU004; latest complete run is the default.",
    )
    return parser.parse_args()


def resolve_branch_runs(
    dataset_root: Path, branch_ids: list[str], requested_run: str | None
) -> tuple[dict[str, Path], dict[str, str]]:
    if requested_run:
        run_root = dataset_root / requested_run
        if all((run_root / branch / "batch-summary.json").is_file() for branch in branch_ids):
            return (
                {branch: run_root / branch for branch in branch_ids},
                {branch: requested_run for branch in branch_ids},
            )
        raise RuntimeError(f"Shared dataset run is incomplete or missing: {run_root}")

    shared_runs = sorted(
        child
        for child in dataset_root.iterdir()
        if child.is_dir()
        and child.name != "analysis"
        and all((child / branch / "batch-summary.json").is_file() for branch in branch_ids)
    )
    if shared_runs:
        run_root = shared_runs[-1]
        return (
            {branch: run_root / branch for branch in branch_ids},
            {branch: run_root.name for branch in branch_ids},
        )

    branch_runs = {}
    labels = {}
    for branch in branch_ids:
        branch_root = dataset_root / branch
        candidates = sorted(
            child
            for child in branch_root.iterdir()
            if child.is_dir() and (child / "batch-summary.json").is_file()
        )
        if not candidates:
            raise RuntimeError(f"No compact dataset found for {branch}")
        branch_runs[branch] = candidates[-1]
        labels[branch] = candidates[-1].name
    return branch_runs, labels


def main() -> None:
    args = parse_args()
    study_root = REPO / "studies" / args.study
    dataset_root = REPO / "datasets" / args.study
    study = json.loads((study_root / "study.json").read_text(encoding="utf-8-sig"))
    if study["board_set_id"] != "BRD001" or int(study["expected_boards"]) != 286:
        raise RuntimeError("Human flop strategy requires the complete 286-board BRD001 set")
    branches = study["branches"]
    branch_ids = [branch["id"] for branch in branches]
    branch_metas = {branch["id"]: analysis.branch_meta(branch) for branch in branches}
    branch_runs, run_labels = resolve_branch_runs(dataset_root, branch_ids, args.run)
    final_root = dataset_root / "analysis"
    narrow_root = final_root / "strategy-13"
    wide_root = final_root / "strategy-8"

    partition = validate_board_partition()
    loaded = {}
    validations = {}
    hashes = {}
    for branch in branch_ids:
        meta = branch_metas[branch]
        source_rows, combo_hashes, validation = analysis.read_branch(
            branch, meta, branch_runs[branch], run_labels[branch]
        )
        loaded[branch] = [remap_hand(row) for row in source_rows]
        validations[branch] = validation
        hashes[branch] = combo_hashes

    support_groups = defaultdict(list)
    for branch in branch_ids:
        support_groups[branch_metas[branch]["actor"]].append(branch)
    for group in support_groups.values():
        for branch in group[1:]:
            if hashes[branch] != hashes[group[0]]:
                raise RuntimeError(f"Combo support mismatch: {group[0]} vs {branch}")

    source = (
        "six tracked STU002 aggregate combo datasets"
        if study["study_id"] == "STU002"
        else f"{len(branch_ids)} tracked {study['study_id']} aggregate combo datasets"
    )
    root_reach = sum(row["reach"] for row in loaded[branch_ids[0]] if row["reach"] > 0)
    narrow = write_model(
        narrow_root,
        "11 hand categories x 13 B13 flop categories",
        source,
        analysis.B13,
        loaded,
        branch_metas,
        root_reach,
        analysis.flop_class,
    )
    narrow_loss = {
        item["branch"]: item["summary"]["root_loss_bb"] for item in narrow["branches"]
    }
    wide = write_model(
        wide_root,
        "11 hand categories x 8 flop categories",
        source,
        [group["name"] for group in FLOP_GROUPS],
        loaded,
        branch_metas,
        root_reach,
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
    source_audit = {
        "board_count": partition["boards"],
        "b13_counts": {name: partition["b13_counts"][name] for name in analysis.B13},
        "b13_expected": analysis.B13_EXPECTED,
        "dataset_validation": validations,
        "source_combo_support_consistent": dict(support_groups),
        "classification": "PASS: every dataset row received exactly one base/direct/BDFD category",
    }
    final_root.mkdir(parents=True, exist_ok=True)
    (final_root / "SOURCE_VALIDATION.json").write_text(
        json.dumps(source_audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (final_root / "FINAL_VALIDATION.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (final_root / "FLOP_GROUPS.json").write_text(
        json.dumps(FLOP_GROUPS, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_analysis_readme(final_root, study, args.study)
    print(json.dumps({
        "status": "PASS",
        "study": args.study,
        "narrow": narrow_root.as_posix(),
        "wide": wide_root.as_posix(),
        "wide_mix_cells": sum(
            sum(count for policy, count in item["summary"]["policy_cell_counts"].items() if "/" in policy)
            for item in wide["branches"]
        ),
        "wide_populated_cells": sum(item["summary"]["populated_cells"] for item in wide["branches"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

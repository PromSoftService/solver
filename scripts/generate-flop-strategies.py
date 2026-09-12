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
    "Weak pair",
    "Third pair",
    "Low pocket pair",
    "OESD",
    "Gutshot",
    "2 overcards + BDFD",
    "Air",
]

FLOP_GROUPS = [
    {"name": "ABB", "count": 6, "members": ["ABB"], "definition": "A with two broadway cards"},
    {"name": "A[K/Q]x", "count": 16, "members": ["A[K/Q]x"], "definition": "A with K/Q and a card 9 or lower"},
    {"name": "A[J-T]x", "count": 16, "members": ["A[J-T][9-5]", "A[J-T][4-2]"], "definition": "A with J/T"},
    {"name": "A[9-2]x", "count": 28, "members": ["A[9-7]x", "A[6-2]x"], "definition": "A with a middle card 9 or lower"},
    {"name": "BBB", "count": 4, "members": ["BBB"], "definition": "No A; three broadway cards"},
    {"name": "BBx", "count": 47, "members": ["BBx"], "definition": "No A; two broadway cards and a card 9 or lower"},
    {"name": "K/Qx", "count": 56, "members": ["K/Qx dis", "K/Qx con"], "definition": "Top card K/Q, excluding BBx"},
    {"name": "[J-8]x dis", "count": 67, "members": ["[J-8]x dis"], "definition": "Top card J/T/9/8; lower two ranks are not adjacent"},
    {"name": "[J-8]x con", "count": 26, "members": ["[J-8]x con"], "definition": "Top card J/T/9/8; lower two ranks are adjacent; includes JT9"},
    {"name": "[7-4]x", "count": 20, "members": ["[7-4]x"], "definition": "Top card 7 or lower"},
]

GROUP_BY_B13 = {
    member: group["name"] for group in FLOP_GROUPS for member in group["members"]
}


def remap_hand(row: dict) -> dict:
    """Map strict base/direct/BDFD data to the accepted 12 learnable rows.

    Direct straight draws take priority over every made-hand base: OESD, then
    Gutshot.  Without a direct draw, made hands keep their base; the remaining
    unmade hands become exactly two overcards with BDFD or Air.
    """
    mapped = dict(row)
    base = row["base"]
    if row["direct"] == "OESD":
        label = "OESD"
    elif row["direct"] == "Gutshot":
        label = "Gutshot"
    elif base in {
        "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
        "Underpair", "Weak pair", "Low pocket pair",
    }:
        label = base
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
    """Aggregate cells and optionally encode fold/call dependence on BDFD.

    Policy frequencies use equal combo means per board followed by equal board
    means per displayed flop category. Reach is only a support filter for
    policy selection and is used as the weight for the EV safety audit.
    """
    actions = meta["actions"]
    active = [row for row in rows if row["reach"] > 0]

    board_hand = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    board_hand_bdfd = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    for row in active:
        key = (row["board"], row["hand_category"])
        split_key = (row["board"], row["hand_category"], row["bdfd"])
        for target in (board_hand[key], board_hand_bdfd[split_key]):
            target["count"] += 1
            for action in actions:
                target["sums"][action] += row["freqs"][action]

    def collapse(source, split: bool):
        result = defaultdict(lambda: {"boards": 0, "sums": defaultdict(float)})
        for key, item in source.items():
            board, hand = key[:2]
            suffix = key[2:] if split else ()
            cell = result[(flop_category_for_board(board), hand, *suffix)]
            cell["boards"] += 1
            for action in actions:
                cell["sums"][action] += item["sums"][action] / item["count"]
        return result

    cells = collapse(board_hand, False)
    split_cells = collapse(board_hand_bdfd, True)
    policies = {}
    details = []
    bdfd_candidates = set()

    for (flop_category, hand), item in cells.items():
        key = (flop_category, hand)
        means = {action: item["sums"][action] / item["boards"] for action in actions}
        policy, probs = analysis.choose_policy(means, actions)
        detail = {
            "flop_category": flop_category,
            "hand_category": hand,
            "boards_present": item["boards"],
            **{f"mean_{action}_frequency": means[action] for action in actions},
            "policy": analysis.display_policy(policy, meta["labels"]),
            "bdfd_rule": False,
            "bdfd_boards_present": 0,
            "no_bdfd_boards_present": 0,
            "bdfd_mean_continue_frequency": "",
            "no_bdfd_mean_fold_frequency": "",
            "active_combos": 0,
            "reach_sum": 0.0,
            "weighted_loss_native": 0.0,
            "max_combo_loss_native": 0.0,
        }
        policies[key] = {"default": probs, "bdfd_rule": False}

        if "fold" in actions and "call" in actions:
            with_draw = split_cells.get((flop_category, hand, True))
            without_draw = split_cells.get((flop_category, hand, False))
            if with_draw and without_draw:
                bdfd_means = {
                    action: with_draw["sums"][action] / with_draw["boards"]
                    for action in actions
                }
                no_bdfd_means = {
                    action: without_draw["sums"][action] / without_draw["boards"]
                    for action in actions
                }
                bdfd_continue = sum(
                    bdfd_means[action] for action in actions if action != "fold"
                )
                detail["bdfd_boards_present"] = with_draw["boards"]
                detail["no_bdfd_boards_present"] = without_draw["boards"]
                detail["bdfd_mean_continue_frequency"] = bdfd_continue
                detail["no_bdfd_mean_fold_frequency"] = no_bdfd_means["fold"]
                if (
                    bdfd_continue > analysis.PURE_THRESHOLD
                    and no_bdfd_means["fold"] > analysis.PURE_THRESHOLD
                ):
                    bdfd_candidates.add(key)
        details.append(detail)

    detail_by_key = {(d["flop_category"], d["hand_category"]): d for d in details}

    # BDFD means fold without BDFD and call with BDFD. Keep the conditional
    # rule only if it is no worse than the ordinary policy in the EV audit.
    default_loss = defaultdict(float)
    bdfd_loss = defaultdict(float)
    for row in active:
        key = (flop_category_for_board(row["board"]), row["hand_category"])
        if key not in bdfd_candidates:
            continue
        default_probs = policies[key]["default"]
        conditional_action = "call" if row["bdfd"] else "fold"
        default_ev = sum(default_probs[action] * row["evs"][action] for action in actions)
        default_loss[key] += row["reach"] * max(0.0, row["mixed_ev"] - default_ev)
        bdfd_loss[key] += row["reach"] * max(
            0.0, row["mixed_ev"] - row["evs"][conditional_action]
        )

    for key in bdfd_candidates:
        if bdfd_loss[key] <= default_loss[key] + 1e-9:
            policies[key]["bdfd_rule"] = True
            detail_by_key[key]["bdfd_rule"] = True
            detail_by_key[key]["policy"] = "BDFD"

    branch_reach = 0.0
    branch_loss = 0.0
    solver_weighted = defaultdict(float)
    simplified_weighted = defaultdict(float)
    for row in active:
        key = (flop_category_for_board(row["board"]), row["hand_category"])
        selected = policies[key]
        if selected["bdfd_rule"]:
            chosen = "call" if row["bdfd"] else "fold"
            probs = {action: float(action == chosen) for action in actions}
        else:
            probs = selected["default"]
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
        "mix_rule": "strict 50/50 top two actions; more frequent action displayed first",
        "bdfd_rule": "BDFD = fold without BDFD, call with BDFD; requires >65% fold/continue split and EV safety",
        "csv_rows": len(rows),
        "active_rows": len(active),
        "zero_reach_rows": len(rows) - len(active),
        "hand_categories": len(HAND_ORDER),
        "populated_cells": len(details),
        "bdfd_cells": sum(d["bdfd_rule"] for d in details),
        "bdfd_candidates_rejected_by_ev": len(bdfd_candidates) - sum(d["bdfd_rule"] for d in details),
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
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "model": model,
        "source": source,
        "pure_threshold": analysis.PURE_THRESHOLD,
        "mix_rule": "strict 50/50 top two actions; more frequent action displayed first",
        "bdfd_rule": (
            "BDFD means fold without BDFD and call with BDFD; no-BDFD fold and "
            "BDFD continue must each exceed 65%, and the call-only continuation "
            "must not add reach-weighted EV loss versus the ordinary cell policy"
        ),
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
        branch_root = root / branch
        write_csv(
            branch_root / "strategy.csv",
            result["matrix"],
            ["hand_category"] + flop_categories,
        )
        detail_fields = [
            "flop_category", "hand_category", "boards_present", "active_combos", "reach_sum",
        ] + [f"mean_{action}_frequency" for action in meta["actions"]]
        detail_fields += [
            "policy", "bdfd_rule", "bdfd_boards_present", "no_bdfd_boards_present",
            "bdfd_mean_continue_frequency", "no_bdfd_mean_fold_frequency",
            "mean_local_loss_bb", "max_combo_loss_bb",
        ]
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
        raise RuntimeError(f"Ten-group mismatch: {dict(group_counts)} != {expected}")
    return {"boards": len(boards), "b13_counts": b13_counts, "group_counts": group_counts}


def validate_pocket_pair_partition() -> dict:
    """Exhaustively verify the four pocket-pair bands on every BRD001 flop."""
    boards = [
        line.strip()
        for line in analysis.BOARD_FILE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    suits = "shdc"
    counts = Counter()
    checked = 0
    for board in boards:
        board_cards = set(analysis.cards(board))
        top, middle, low = sorted(
            (analysis.rank(card) for card in board_cards), reverse=True
        )
        for rank_char, pair_rank in analysis.RANK_VALUE.items():
            available = [rank_char + suit for suit in suits if rank_char + suit not in board_cards]
            for first_index in range(len(available)):
                for second_index in range(first_index + 1, len(available)):
                    combo = available[first_index] + available[second_index]
                    base, _, _, _ = analysis.hand_category(board, combo)
                    if pair_rank in {top, middle, low}:
                        expected = "Two pair+"
                    elif pair_rank > top:
                        expected = "Overpair"
                    elif top > pair_rank > middle:
                        expected = "Underpair"
                    elif middle > pair_rank > low:
                        expected = "Weak pair"
                    else:
                        expected = "Low pocket pair"
                    if base != expected:
                        raise RuntimeError(
                            f"Pocket-pair partition mismatch: {board} {combo} "
                            f"classified {base}, expected {expected}"
                        )
                    counts[base] += 1
                    checked += 1
    for required in ("Two pair+", "Overpair", "Underpair", "Weak pair", "Low pocket pair"):
        if counts[required] == 0:
            raise RuntimeError(f"Pocket-pair partition has no examples for {required}")
    return {"status": "PASS", "checked": checked, "base_counts": dict(counts)}


def write_analysis_readme(root: Path, study: dict, study_directory: str) -> None:
    code = study["study_id"]
    text = f"""# {code} active strategy outputs

This directory contains the reproducible machine-readable strategy, validation
audits and one human workbook for `{study_directory}`.

Human workbook:

- `{code}_flop_strategy.xlsx` — 12 hand rows by the final 10 flop categories.

Machine-readable outputs:

- `strategy-10/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the numeric strategy directly from tracked solver combo frequencies:

```text
python scripts/generate-flop-strategies.py {study_directory}
```

Build the workbook with the approved colors and layout:

```text
node scripts/build-flop-workbooks.mjs {study_directory}
```

`BDFD` in a cell means fold without a backdoor flush draw and call with one.
The full method and range provenance are in `docs/FLOP_STRATEGY_WORKFLOW.md`.
Rejected horizontal smoothing experiments remain only in Git history.
"""
    (root / "README.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the final ten-category human flop strategy from solver combos."
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
    model_root = final_root / "strategy-10"

    partition = validate_board_partition()
    pocket_pair_partition = validate_pocket_pair_partition()
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

    source = f"{len(branch_ids)} tracked {study['study_id']} aggregate combo datasets"
    root_reach = sum(row["reach"] for row in loaded[branch_ids[0]] if row["reach"] > 0)
    model = write_model(
        model_root,
        "12 hand categories x 10 final flop categories",
        source,
        [group["name"] for group in FLOP_GROUPS],
        loaded,
        branch_metas,
        root_reach,
        lambda board: GROUP_BY_B13[analysis.flop_class(board)],
    )
    branch_audit = {
        item["branch"]: {
            "populated_cells": item["summary"]["populated_cells"],
            "bdfd_cells": item["summary"]["bdfd_cells"],
            "bdfd_candidates_rejected_by_ev": item["summary"]["bdfd_candidates_rejected_by_ev"],
            "root_loss_bb": item["summary"]["root_loss_bb"],
        }
        for item in model["branches"]
    }
    audit = {
        "status": "PASS",
        "boards": partition["boards"],
        "b13_counts": {name: partition["b13_counts"][name] for name in analysis.B13},
        "ten_group_counts": {
            group["name"]: partition["group_counts"][group["name"]] for group in FLOP_GROUPS
        },
        "hand_rows": HAND_ORDER,
        "dataset_validation": validations,
        "source_combo_support_consistent": True,
        "pocket_pair_partition": pocket_pair_partition,
        "branch_strategy_audit": branch_audit,
        "classification": (
            "Every source combo has exactly one base category, one direct-draw state, "
            "one BDFD state, and exactly one displayed hand row. Display priority is "
            "OESD, Gutshot, made hand, two overcards plus BDFD, Air."
        ),
        "bdfd_cell_rule": (
            "BDFD means fold without BDFD and call with BDFD. No-BDFD fold and "
            "BDFD continue must each exceed 65%; then call-only continuation must pass the EV audit."
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
        "pocket_pair_partition": pocket_pair_partition,
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
        "model": model_root.as_posix(),
        "mix_cells": sum(
            sum(count for policy, count in item["summary"]["policy_cell_counts"].items() if "/" in policy)
            for item in model["branches"]
        ),
        "bdfd_cells": sum(item["summary"]["bdfd_cells"] for item in model["branches"]),
        "populated_cells": sum(item["summary"]["populated_cells"] for item in model["branches"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

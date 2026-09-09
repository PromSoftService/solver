from __future__ import annotations

import csv
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "layered-smooth-12"
ROOT_EXTRA_CAP_BB = 0.001
NODE_EXTRA_CAP_BB = 0.01
MADE = [
    "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
    "Underpair", "Weak pair",
]
HAND_ORDER = MADE + [
    "OESD", "Gutshot", "2 overcards + BDFD", "A-high + BDFD", "Air",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load_module("analyze_stu002", REPO / "scripts" / "analyze-stu002.py")
a.hand_sort_key = lambda label: HAND_ORDER.index(label)
OUTPUT = a.OUT_ROOT / OUTPUT_NAME


def remap(rows: list[dict]) -> list[dict]:
    mapped = []
    for source in rows:
        row = source.copy()
        base = row["base"]
        if base in MADE:
            category = base
        elif row["direct"] == "OESD":
            category = "OESD"
        elif row["direct"] == "Gutshot":
            category = "Gutshot"
        elif row["bdfd"] and base == "2 overcards":
            category = "2 overcards + BDFD"
        elif row["bdfd"] and base == "A-high":
            category = "A-high + BDFD"
        else:
            category = "Air"
        row["hand_category"] = category
        mapped.append(row)
    return mapped


def policy_probs(policy: str, actions: list[str]) -> dict[str, float]:
    selected = policy.split("/")
    return {action: (1.0 / len(selected) if action in selected else 0.0) for action in actions}


def policy_display(policy: str, labels: dict[str, str]) -> str:
    return a.display_policy(policy, labels)


def possible_policies(actions: list[str]) -> list[str]:
    policies = list(actions)
    policies.extend("/".join(pair) for pair in itertools.combinations(actions, 2))
    return policies


def cell_means(rows: list[dict], actions: list[str]) -> dict[tuple[str, str], dict[str, float]]:
    board_hand = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    for row in rows:
        if row["reach"] <= 0:
            continue
        key = (row["board"], row["hand_category"])
        board_hand[key]["count"] += 1
        for action in actions:
            board_hand[key]["sums"][action] += row["freqs"][action]
    cells = defaultdict(lambda: {"boards": 0, "sums": defaultdict(float)})
    for (board, hand), item in board_hand.items():
        key = (a.flop_class(board), hand)
        cells[key]["boards"] += 1
        for action in actions:
            cells[key]["sums"][action] += item["sums"][action] / item["count"]
    return {
        key: {action: item["sums"][action] / item["boards"] for action in actions}
        for key, item in cells.items()
    }


def loss_tables(
    rows: list[dict], actions: list[str], policies: list[str]
) -> tuple[dict[tuple[str, str, str], float], dict[str, float], float]:
    losses = defaultdict(float)
    reaches = defaultdict(float)
    branch_reach = 0.0
    probs = {policy: policy_probs(policy, actions) for policy in policies}
    for row in rows:
        if row["reach"] <= 0:
            continue
        key = (row["hand_category"], row["flop_class"])
        reaches[row["hand_category"]] += row["reach"]
        branch_reach += row["reach"]
        for policy in policies:
            simple_ev = sum(probs[policy][action] * row["evs"][action] for action in actions)
            loss = max(0.0, row["mixed_ev"] - simple_ev)
            losses[(key[0], key[1], policy)] += row["reach"] * loss
    return losses, reaches, branch_reach


def frequency_score(
    sequence: tuple[str, ...], means: list[dict[str, float]], actions: list[str]
) -> float:
    score = 0.0
    for policy, cell in zip(sequence, means):
        probs = policy_probs(policy, actions)
        score += 0.5 * sum(abs(cell[action] - probs[action]) for action in actions)
    return score / len(sequence)


def raw_sequence(means: list[dict[str, float]], actions: list[str]) -> tuple[str, ...]:
    sequence = []
    for cell in means:
        policy = a.choose_policy(cell, actions)[0]
        selected = set(policy.split("/"))
        sequence.append("/".join(action for action in actions if action in selected))
    return tuple(sequence)


def structured_candidates(
    means: list[dict[str, float]], actions: list[str]
) -> list[dict]:
    n = len(means)
    action_index = {action: index for index, action in enumerate(actions)}
    policies = possible_policies(actions)
    best = {}
    for blocks in range(1, min(3, n) + 1):
        for cuts in itertools.combinations(range(1, n), blocks - 1):
            bounds = (0,) + cuts + (n,)
            for block_policies in itertools.product(policies, repeat=blocks):
                if any(block_policies[i] == block_policies[i + 1] for i in range(blocks - 1)):
                    continue
                sequence = []
                for index in range(n):
                    block = next(i for i in range(blocks) if bounds[i] <= index < bounds[i + 1])
                    sequence.append(block_policies[block])
                sequence_tuple = tuple(sequence)
                mix_cells = sum("/" in policy for policy in sequence_tuple)
                score = frequency_score(sequence_tuple, means, actions)
                tie = tuple(
                    tuple(action_index[action] for action in policy.split("/"))
                    for policy in sequence_tuple
                )
                candidate = {
                    "sequence": sequence_tuple,
                    "blocks": blocks,
                    "mix_cells": mix_cells,
                    "score": score,
                    "tie": tie,
                    "kind": "structured",
                }
                previous = best.get(blocks)
                if previous is None or (score, mix_cells, tie) < (
                    previous["score"], previous["mix_cells"], previous["tie"]
                ):
                    best[blocks] = candidate
    candidates = [best[key] for key in sorted(best)]
    raw = raw_sequence(means, actions)
    candidates.append({
        "sequence": raw,
        "blocks": 99,
        "mix_cells": sum("/" in policy for policy in raw),
        "score": frequency_score(raw, means, actions),
        "tie": (),
        "kind": "raw",
    })
    return candidates


def candidate_loss(
    hand: str, flop_classes: list[str], sequence: tuple[str, ...], losses: dict
) -> float:
    return sum(losses[(hand, flop_class, policy)] for flop_class, policy in zip(flop_classes, sequence))


def actual_transitions(sequence: tuple[str, ...]) -> int:
    return sum(left != right for left, right in zip(sequence, sequence[1:]))


def build_options(rows: list[dict], meta: dict) -> tuple[dict, dict, float, dict]:
    actions = meta["actions"]
    policies = possible_policies(actions)
    means_by_cell = cell_means(rows, actions)
    losses, reaches, branch_reach = loss_tables(rows, actions, policies)
    options = {}
    raw_policy_map = {}
    raw_loss = 0.0
    for hand in HAND_ORDER:
        flop_classes = [fc for fc in a.B13 if (fc, hand) in means_by_cell]
        if not flop_classes:
            continue
        means = [means_by_cell[(fc, hand)] for fc in flop_classes]
        row_options = structured_candidates(means, actions)
        for option in row_options:
            option["loss_native"] = candidate_loss(
                hand, flop_classes, option["sequence"], losses
            )
            option["complexity_value"] = (
                100 if option["kind"] == "raw"
                else option["blocks"] - 1
            )
        raw = row_options[-1]
        raw_loss += raw["loss_native"]
        raw_policy_map.update({(fc, hand): policy for fc, policy in zip(flop_classes, raw["sequence"])})
        options[hand] = {"flop_classes": flop_classes, "items": row_options, "reach": reaches[hand]}
    return options, raw_policy_map, raw_loss, {
        "means": means_by_cell, "losses": losses, "branch_reach": branch_reach,
    }


def select_options(options: dict, raw_loss: float, branch_reach: float, root_reach: float) -> dict:
    max_extra_native = min(
        ROOT_EXTRA_CAP_BB * root_reach * a.EV_SCALE_PER_BB,
        NODE_EXTRA_CAP_BB * branch_reach * a.EV_SCALE_PER_BB,
    )
    target = raw_loss + max_extra_native
    selected = {hand: 0 for hand in options}

    def total_loss() -> float:
        return sum(options[hand]["items"][index]["loss_native"] for hand, index in selected.items())

    while total_loss() > target + 1e-9:
        upgrades = []
        for hand, index in selected.items():
            current = options[hand]["items"][index]
            for next_index in range(index + 1, len(options[hand]["items"])):
                candidate = options[hand]["items"][next_index]
                reduction = current["loss_native"] - candidate["loss_native"]
                if reduction <= 1e-9:
                    continue
                complexity = max(1, candidate["complexity_value"] - current["complexity_value"])
                upgrades.append((reduction / complexity, reduction, hand, next_index))
        if not upgrades:
            raise RuntimeError("No smoothing upgrade can satisfy EV cap")
        _, _, hand, next_index = max(upgrades)
        selected[hand] = next_index

    while True:
        current_total = total_loss()
        simplifications = []
        for hand, index in selected.items():
            if index == 0:
                continue
            current = options[hand]["items"][index]
            for earlier_index in range(index):
                candidate = options[hand]["items"][earlier_index]
                added_loss = candidate["loss_native"] - current["loss_native"]
                if current_total + added_loss > target + 1e-9:
                    continue
                complexity_reduction = current["complexity_value"] - candidate["complexity_value"]
                simplifications.append(
                    (complexity_reduction, -max(0.0, added_loss), hand, earlier_index)
                )
        if not simplifications:
            break
        _, _, hand, earlier_index = max(simplifications)
        selected[hand] = earlier_index
    return {
        "selected": selected,
        "target_loss_native": target,
        "max_extra_native": max_extra_native,
        "total_loss_native": total_loss(),
    }


def policy_map_from_selection(options: dict, selected: dict) -> dict[tuple[str, str], str]:
    result = {}
    for hand, index in selected.items():
        row = options[hand]
        sequence = row["items"][index]["sequence"]
        result.update({(fc, hand): policy for fc, policy in zip(row["flop_classes"], sequence)})
    return result


def evaluate_policy(rows: list[dict], meta: dict, policy_map: dict, root_reach: float) -> dict:
    actions = meta["actions"]
    solver_weighted = defaultdict(float)
    simple_weighted = defaultdict(float)
    weighted_loss = 0.0
    branch_reach = 0.0
    for row in rows:
        if row["reach"] <= 0:
            continue
        policy = policy_map[(row["flop_class"], row["hand_category"])]
        probs = policy_probs(policy, actions)
        simple_ev = sum(probs[action] * row["evs"][action] for action in actions)
        weighted_loss += row["reach"] * max(0.0, row["mixed_ev"] - simple_ev)
        branch_reach += row["reach"]
        for action in actions:
            solver_weighted[action] += row["reach"] * row["freqs"][action]
            simple_weighted[action] += row["reach"] * probs[action]
    return {
        "weighted_loss_native": weighted_loss,
        "root_loss_bb": weighted_loss / root_reach / a.EV_SCALE_PER_BB,
        "node_loss_bb": weighted_loss / branch_reach / a.EV_SCALE_PER_BB,
        "reach_sum": branch_reach,
        "solver_frequencies": {action: solver_weighted[action] / branch_reach for action in actions},
        "simplified_frequencies": {action: simple_weighted[action] / branch_reach for action in actions},
        "policy_cell_counts": dict(Counter(policy_display(p, meta["labels"]) for p in policy_map.values())),
    }


def matrix_rows(policy_map: dict, meta: dict) -> list[dict]:
    rows = []
    for hand in HAND_ORDER:
        if not any((fc, hand) in policy_map for fc in a.B13):
            continue
        rows.append({
            "hand_category": hand,
            **{
                fc: policy_display(policy_map[(fc, hand)], meta["labels"])
                if (fc, hand) in policy_map else "—"
                for fc in a.B13
            },
        })
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    loaded = {}
    for branch, meta in a.BRANCHES.items():
        source_rows, _, _ = a.read_branch(branch, meta)
        loaded[branch] = remap(source_rows)
    root_reach = sum(row["reach"] for row in loaded["01_BB_FIRST"] if row["reach"] > 0)

    manifest = {
        "model": OUTPUT_NAME,
        "categories": HAND_ORDER,
        "root_extra_cap_bb_per_branch": ROOT_EXTRA_CAP_BB,
        "node_extra_cap_bb_per_branch": NODE_EXTRA_CAP_BB,
        "smoothing": "at most 3 contiguous action blocks; each block is pure or a strict 50/50 mix",
        "branches": [],
    }
    for branch, meta in a.BRANCHES.items():
        rows = loaded[branch]
        options, raw_map, raw_loss, context = build_options(rows, meta)
        selection = select_options(
            options, raw_loss, context["branch_reach"], root_reach
        )
        smooth_map = policy_map_from_selection(options, selection["selected"])
        raw_eval = evaluate_policy(rows, meta, raw_map, root_reach)
        smooth_eval = evaluate_policy(rows, meta, smooth_map, root_reach)
        branch_out = OUTPUT / branch
        write_csv(
            branch_out / "strategy-raw.csv", matrix_rows(raw_map, meta),
            ["hand_category"] + a.B13,
        )
        write_csv(
            branch_out / "strategy.csv", matrix_rows(smooth_map, meta),
            ["hand_category"] + a.B13,
        )
        audit_rows = []
        for hand in HAND_ORDER:
            if hand not in options:
                continue
            row = options[hand]
            raw_option = row["items"][-1]
            chosen = row["items"][selection["selected"][hand]]
            raw_display = [policy_display(policy, meta["labels"]) for policy in raw_option["sequence"]]
            smooth_display = [policy_display(policy, meta["labels"]) for policy in chosen["sequence"]]
            audit_rows.append({
                "hand_category": hand,
                "present_cells": len(row["flop_classes"]),
                "raw_transitions": actual_transitions(raw_option["sequence"]),
                "smoothed_blocks": chosen["blocks"] if chosen["kind"] == "structured" else "raw",
                "smoothed_mix_cells": chosen["mix_cells"],
                "frequency_distance": chosen["score"],
                "raw_root_loss_bb": raw_option["loss_native"] / root_reach / a.EV_SCALE_PER_BB,
                "smoothed_root_loss_bb": chosen["loss_native"] / root_reach / a.EV_SCALE_PER_BB,
                "incremental_root_loss_bb": (
                    chosen["loss_native"] - raw_option["loss_native"]
                ) / root_reach / a.EV_SCALE_PER_BB,
                "options": "; ".join(
                    f'{option["kind"]}:{option["blocks"]}='
                    f'{option["loss_native"] / root_reach / a.EV_SCALE_PER_BB:.9f}'
                    for option in row["items"]
                ),
                "raw_pattern": " | ".join(raw_display),
                "smoothed_pattern": " | ".join(smooth_display),
            })
        write_csv(
            branch_out / "row-audit.csv", audit_rows,
            [
                "hand_category", "present_cells", "raw_transitions", "smoothed_blocks",
                "smoothed_mix_cells", "frequency_distance", "raw_root_loss_bb",
                "smoothed_root_loss_bb", "incremental_root_loss_bb", "options",
                "raw_pattern", "smoothed_pattern",
            ],
        )
        summary = {
            "branch": branch,
            "acting_player": meta["actor"],
            "action_shape": meta["shape"],
            "raw": raw_eval,
            "smoothed": smooth_eval,
            "incremental_root_loss_bb": smooth_eval["root_loss_bb"] - raw_eval["root_loss_bb"],
            "incremental_node_loss_bb": smooth_eval["node_loss_bb"] - raw_eval["node_loss_bb"],
            "selection_target_root_loss_bb": (
                selection["target_loss_native"] / root_reach / a.EV_SCALE_PER_BB
            ),
            "selection_total_root_loss_bb": (
                selection["total_loss_native"] / root_reach / a.EV_SCALE_PER_BB
            ),
            "selected_rows": {
                hand: {
                    "kind": options[hand]["items"][index]["kind"],
                    "blocks": options[hand]["items"][index]["blocks"],
                    "mix_cells": options[hand]["items"][index]["mix_cells"],
                }
                for hand, index in selection["selected"].items()
            },
        }
        (branch_out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest["branches"].append(summary)
    manifest["sum_raw_root_loss_bb"] = sum(
        branch["raw"]["root_loss_bb"] for branch in manifest["branches"]
    )
    manifest["sum_smoothed_root_loss_bb"] = sum(
        branch["smoothed"]["root_loss_bb"] for branch in manifest["branches"]
    )
    manifest["sum_incremental_root_loss_bb"] = (
        manifest["sum_smoothed_root_loss_bb"] - manifest["sum_raw_root_loss_bb"]
    )
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "sum_raw_root_loss_bb": manifest["sum_raw_root_loss_bb"],
        "sum_smoothed_root_loss_bb": manifest["sum_smoothed_root_loss_bb"],
        "sum_incremental_root_loss_bb": manifest["sum_incremental_root_loss_bb"],
        "branches": [
            {
                "branch": branch["branch"],
                "raw": branch["raw"]["root_loss_bb"],
                "smoothed": branch["smoothed"]["root_loss_bb"],
                "incremental_root": branch["incremental_root_loss_bb"],
                "incremental_node": branch["incremental_node_loss_bb"],
                "rows": branch["selected_rows"],
            }
            for branch in manifest["branches"]
        ],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

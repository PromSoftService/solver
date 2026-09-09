from __future__ import annotations

import csv
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "clustered-13-smooth-v2"
MAX_INITIAL_BLOCKS = 3
GLOBAL_DRIFT_CAP = 0.015
CLASS_DRIFT_CAP = 0.15
ROOT_LOSS_DELTA_CAP_BB = 0.00025


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


g = load_module("generate_stu002_clustered", REPO / "scripts" / "generate-stu002-clustered.py")
a = g.analysis
OUTPUT = a.OUT_ROOT / OUTPUT_NAME
HAND_ORDER = [
    "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
    "Underpair", "Weak pair", "2 overcards", "2 overcards + draw",
    "A-high", "A-high + draw", "Air", "Air + draw",
]
B13_COUNTS = {
    "ABB": 6, "A[K/Q]x": 16, "A[J-T][9-5]": 10, "A[J-T][4-2]": 6,
    "A[9-7]x": 18, "A[6-2]x": 10, "BBB": 4, "BBx": 47,
    "K/Qx dis": 42, "K/Qx con": 14, "[J-8]x dis": 67,
    "[J-8]x con": 26, "[7-4]x": 20,
}


def canonical_policy(policy: str, actions: list[str]) -> str:
    selected = set(policy.split("/"))
    return "/".join(action for action in actions if action in selected)


def policy_probs(policy: str, actions: list[str]) -> dict[str, float]:
    selected = policy.split("/")
    return {action: (1.0 / len(selected) if action in selected else 0.0) for action in actions}


def possible_policies(actions: list[str]) -> list[str]:
    return list(actions) + ["/".join(pair) for pair in itertools.combinations(actions, 2)]


def tv(left: str, right: str, actions: list[str]) -> float:
    lp = policy_probs(left, actions)
    rp = policy_probs(right, actions)
    return 0.5 * sum(abs(lp[action] - rp[action]) for action in actions)


def blocks(sequence: tuple[str, ...]) -> int:
    if not sequence:
        return 0
    return 1 + sum(left != right for left, right in zip(sequence, sequence[1:]))


def build_raw(rows: list[dict], meta: dict) -> tuple[dict, dict, dict]:
    actions = meta["actions"]
    board_hand = defaultdict(lambda: {"count": 0, "sums": defaultdict(float)})
    for row in rows:
        if row["reach"] <= 0:
            continue
        item = board_hand[(row["board"], row["hand_category"])]
        item["count"] += 1
        for action in actions:
            item["sums"][action] += row["freqs"][action]

    cells = defaultdict(lambda: {"boards": 0, "sums": defaultdict(float)})
    for (board, hand), item in board_hand.items():
        key = (a.flop_class(board), hand)
        cells[key]["boards"] += 1
        for action in actions:
            cells[key]["sums"][action] += item["sums"][action] / item["count"]

    raw_map = {}
    means = {}
    board_counts = {}
    for key, item in cells.items():
        cell = {action: item["sums"][action] / item["boards"] for action in actions}
        raw_map[key] = canonical_policy(a.choose_policy(cell, actions)[0], actions)
        means[key] = cell
        board_counts[key] = item["boards"]
    return raw_map, means, board_counts


def best_sequence(
    raw: tuple[str, ...], weights: tuple[int, ...], actions: list[str], max_blocks: int
) -> dict:
    if blocks(raw) <= max_blocks:
        return {"sequence": raw, "distance": 0.0, "pure_changes": 0,
                "mix_changes": 0, "blocks": blocks(raw)}
    policies = possible_policies(actions)
    policy_rank = {policy: index for index, policy in enumerate(policies)}

    def cell_cost(old: str, new: str, weight: int) -> tuple[float, int, int, int]:
        return (
            weight * tv(old, new, actions),
            int(old != new and "/" not in old),
            int(old != new and "/" in new and "/" not in old),
            int(old != new and "/" in old),
        )

    # Dynamic programming state: (used blocks, last policy) -> cumulative
    # (distance numerator, pure changes, introduced mixes, changed mixes, sequence).
    states = {}
    for policy in policies:
        cost = cell_cost(raw[0], policy, weights[0])
        states[(1, policy)] = (*cost, (policy,))
    for pos in range(1, len(raw)):
        next_states = {}
        for (used, last), value in states.items():
            for policy in policies:
                new_used = used + int(policy != last)
                if new_used > max_blocks:
                    continue
                extra = cell_cost(raw[pos], policy, weights[pos])
                candidate = (
                    value[0] + extra[0], value[1] + extra[1],
                    value[2] + extra[2], value[3] + extra[3],
                    value[4] + (policy,),
                )
                key = (new_used, policy)
                current = next_states.get(key)
                candidate_tie = (candidate[1], candidate[0], candidate[2], candidate[3]) + (
                    tuple(policy_rank[x] for x in candidate[4]),
                )
                if current is None:
                    next_states[key] = candidate
                else:
                    current_tie = (current[1], current[0], current[2], current[3]) + (
                        tuple(policy_rank[x] for x in current[4]),
                    )
                    if candidate_tie < current_tie:
                        next_states[key] = candidate
        states = next_states

    best = None
    for (used, _), value in states.items():
        candidate = (value[1], value[0], value[2], value[3], -used,
                     tuple(policy_rank[x] for x in value[4]), value[4])
        if best is None or candidate[:-1] < best[:-1]:
            best = candidate
    if best is None:
        raise RuntimeError("No smoothing candidate")
    return {
        "sequence": best[-1], "distance": best[1] / sum(weights), "pure_changes": best[0],
        "mix_changes": best[3], "blocks": blocks(best[-1]),
    }


def row_options(raw_map: dict, board_counts: dict, meta: dict) -> dict:
    actions = meta["actions"]
    result = {}
    for hand in HAND_ORDER:
        classes = [fc for fc in a.B13 if (fc, hand) in raw_map]
        if not classes:
            continue
        raw = tuple(raw_map[(fc, hand)] for fc in classes)
        weights = tuple(board_counts[(fc, hand)] for fc in classes)
        raw_blocks = blocks(raw)
        items = {}
        for limit in range(1, raw_blocks + 1):
            items[limit] = best_sequence(raw, weights, actions, limit)
        result[hand] = {"classes": classes, "raw": raw, "raw_blocks": raw_blocks,
                        "items": items}
    return result


def map_from_selection(options: dict, selected: dict) -> dict:
    result = {}
    for hand, item in options.items():
        sequence = item["items"][selected[hand]]["sequence"]
        result.update({(fc, hand): policy for fc, policy in zip(item["classes"], sequence)})
    return result


def evaluate(rows: list[dict], meta: dict, policy_map: dict, root_reach: float) -> dict:
    actions = meta["actions"]
    branch_reach = 0.0
    loss_native = 0.0
    solver = defaultdict(float)
    simple = defaultdict(float)
    class_reach = defaultdict(float)
    class_simple = defaultdict(lambda: defaultdict(float))
    for row in rows:
        if row["reach"] <= 0:
            continue
        policy = policy_map[(row["flop_class"], row["hand_category"])]
        probs = policy_probs(policy, actions)
        simple_ev = sum(probs[action] * row["evs"][action] for action in actions)
        loss_native += row["reach"] * max(0.0, row["mixed_ev"] - simple_ev)
        branch_reach += row["reach"]
        class_reach[row["flop_class"]] += row["reach"]
        for action in actions:
            solver[action] += row["reach"] * row["freqs"][action]
            simple[action] += row["reach"] * probs[action]
            class_simple[row["flop_class"]][action] += row["reach"] * probs[action]
    return {
        "root_loss_bb": loss_native / root_reach / a.EV_SCALE_PER_BB,
        "node_loss_bb": loss_native / branch_reach / a.EV_SCALE_PER_BB,
        "reach_sum": branch_reach,
        "solver_frequencies": {action: solver[action] / branch_reach for action in actions},
        "simplified_frequencies": {action: simple[action] / branch_reach for action in actions},
        "class_frequencies": {
            fc: {action: class_simple[fc][action] / class_reach[fc] for action in actions}
            for fc in a.B13 if class_reach[fc] > 0
        },
        "policy_cell_counts": dict(Counter(a.display_policy(p, meta["labels"]) for p in policy_map.values())),
    }


def drift(candidate: dict, raw: dict, actions: list[str]) -> tuple[float, float]:
    global_max = max(
        abs(candidate["simplified_frequencies"][action] - raw["simplified_frequencies"][action])
        for action in actions
    )
    class_max = max(
        abs(candidate["class_frequencies"][fc][action] - raw["class_frequencies"][fc][action])
        for fc in raw["class_frequencies"] for action in actions
    )
    return global_max, class_max


def violation(candidate: dict, raw: dict, actions: list[str]) -> tuple[float, dict]:
    global_max, class_max = drift(candidate, raw, actions)
    root_delta = candidate["root_loss_bb"] - raw["root_loss_bb"]
    score = (
        max(0.0, global_max - GLOBAL_DRIFT_CAP) / GLOBAL_DRIFT_CAP
        + max(0.0, class_max - CLASS_DRIFT_CAP) / CLASS_DRIFT_CAP
        + max(0.0, root_delta - ROOT_LOSS_DELTA_CAP_BB) / ROOT_LOSS_DELTA_CAP_BB
    )
    return score, {"global_max": global_max, "class_max": class_max,
                   "root_loss_delta_bb": root_delta}


def choose_selection(rows: list[dict], meta: dict, options: dict, raw_eval: dict,
                     root_reach: float) -> tuple[dict, dict, dict]:
    selected = {
        hand: min(MAX_INITIAL_BLOCKS, item["raw_blocks"])
        for hand, item in options.items()
    }
    while True:
        policy_map = map_from_selection(options, selected)
        current_eval = evaluate(rows, meta, policy_map, root_reach)
        current_score, current_drift = violation(current_eval, raw_eval, meta["actions"])
        if current_score <= 1e-12:
            return selected, current_eval, current_drift
        upgrades = []
        for hand, limit in selected.items():
            if limit >= options[hand]["raw_blocks"]:
                continue
            trial = dict(selected)
            trial[hand] = limit + 1
            trial_eval = evaluate(rows, meta, map_from_selection(options, trial), root_reach)
            trial_score, trial_drift = violation(trial_eval, raw_eval, meta["actions"])
            distance_reduction = (
                options[hand]["items"][limit]["distance"]
                - options[hand]["items"][limit + 1]["distance"]
            )
            upgrades.append((current_score - trial_score, distance_reduction,
                             hand, trial_eval, trial_drift))
        if not upgrades:
            return selected, current_eval, current_drift
        improvement, _, hand, _, _ = max(upgrades)
        if improvement <= 1e-12:
            # Fall back toward the accepted raw table instead of gaming EV.
            hand = max(
                (h for h in selected if selected[h] < options[h]["raw_blocks"]),
                key=lambda h: options[h]["items"][selected[h]]["distance"]
            )
        selected[hand] += 1


def matrix_rows(policy_map: dict, meta: dict) -> list[dict]:
    return [
        {"hand_category": hand, **{
            fc: a.display_policy(policy_map[(fc, hand)], meta["labels"])
            if (fc, hand) in policy_map else "—" for fc in a.B13
        }}
        for hand in HAND_ORDER if any((fc, hand) in policy_map for fc in a.B13)
    ]


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
        source, _, _ = a.read_branch(branch, meta)
        loaded[branch] = g.recommended_rows(source)
    root_reach = sum(row["reach"] for row in loaded["01_BB_FIRST"] if row["reach"] > 0)
    manifest = {
        "model": OUTPUT_NAME,
        "source": "clustered-13",
        "rule": "minimum policy-profile distortion; keep raw rows already at <=3 blocks",
        "initial_max_blocks": MAX_INITIAL_BLOCKS,
        "global_action_drift_cap": GLOBAL_DRIFT_CAP,
        "b13_class_action_drift_cap": CLASS_DRIFT_CAP,
        "root_loss_delta_cap_bb_per_branch": ROOT_LOSS_DELTA_CAP_BB,
        "branches": [],
    }
    for branch, meta in a.BRANCHES.items():
        rows = loaded[branch]
        raw_map, _, board_counts = build_raw(rows, meta)
        options = row_options(raw_map, board_counts, meta)
        raw_eval = evaluate(rows, meta, raw_map, root_reach)
        selected, smooth_eval, drift_values = choose_selection(
            rows, meta, options, raw_eval, root_reach
        )
        smooth_map = map_from_selection(options, selected)
        audits = []
        for hand, item in options.items():
            choice = item["items"][selected[hand]]
            audits.append({
                "hand_category": hand,
                "raw_blocks": item["raw_blocks"],
                "smoothed_blocks": choice["blocks"],
                "policy_distance": choice["distance"],
                "pure_cells_changed": choice["pure_changes"],
                "mix_cells_changed": choice["mix_changes"],
                "raw_pattern": " | ".join(a.display_policy(x, meta["labels"]) for x in item["raw"]),
                "smoothed_pattern": " | ".join(a.display_policy(x, meta["labels"]) for x in choice["sequence"]),
            })
        out = OUTPUT / branch
        write_csv(out / "strategy-raw.csv", matrix_rows(raw_map, meta), ["hand_category"] + a.B13)
        write_csv(out / "strategy.csv", matrix_rows(smooth_map, meta), ["hand_category"] + a.B13)
        write_csv(out / "row-audit.csv", audits, [
            "hand_category", "raw_blocks", "smoothed_blocks", "policy_distance",
            "pure_cells_changed", "mix_cells_changed", "raw_pattern", "smoothed_pattern",
        ])
        summary = {
            "branch": branch,
            "raw": raw_eval,
            "smoothed": smooth_eval,
            "global_action_drift": drift_values["global_max"],
            "max_b13_class_action_drift": drift_values["class_max"],
            "incremental_root_loss_bb": drift_values["root_loss_delta_bb"],
            "rows": {
                hand: {"raw_blocks": item["raw_blocks"],
                       "smoothed_blocks": item["items"][selected[hand]]["blocks"],
                       "policy_distance": item["items"][selected[hand]]["distance"]}
                for hand, item in options.items()
            },
        }
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest["branches"].append(summary)
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        branch["branch"]: {
            "raw_simple": branch["raw"]["simplified_frequencies"],
            "smooth_simple": branch["smoothed"]["simplified_frequencies"],
            "global_drift": branch["global_action_drift"],
            "class_drift": branch["max_b13_class_action_drift"],
            "root_loss_delta_bb": branch["incremental_root_loss_bb"],
            "changed_rows": {
                hand: row for hand, row in branch["rows"].items()
                if row["raw_blocks"] != row["smoothed_blocks"]
            },
        } for branch in manifest["branches"]
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


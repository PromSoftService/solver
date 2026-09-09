from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MADE = [
    "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
    "Underpair", "Weak pair",
]


def load_analysis():
    path = REPO / "scripts" / "analyze-stu002.py"
    spec = importlib.util.spec_from_file_location("analyze_stu002", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load_analysis()
DISPLAY_ORDER = MADE + [
    "OESD", "Gutshot", "2 overcards + BDFD", "A-high + BDFD",
    "Overcards/A-high + BDFD", "BDFD", "Air",
]
a.hand_sort_key = lambda label: DISPLAY_ORDER.index(label)


def remap(rows: list[dict], model: str) -> list[dict]:
    result = []
    for source in rows:
        row = copy.copy(source)
        base = row["base"]
        if base in MADE:
            category = base
        elif row["direct"] == "OESD":
            category = "OESD"
        elif row["direct"] == "Gutshot":
            category = "Gutshot"
        elif model == "separate-high-bdfd" and row["bdfd"] and base == "2 overcards":
            category = "2 overcards + BDFD"
        elif model == "separate-high-bdfd" and row["bdfd"] and base == "A-high":
            category = "A-high + BDFD"
        elif model == "combined-high-bdfd" and row["bdfd"] and base in {"2 overcards", "A-high"}:
            category = "Overcards/A-high + BDFD"
        elif model == "all-bdfd" and row["bdfd"]:
            category = "BDFD"
        else:
            category = "Air"
        row["hand_category"] = category
        result.append(row)
    return result


def main() -> None:
    loaded = {}
    for branch, meta in a.BRANCHES.items():
        rows, _, _ = a.read_branch(branch, meta)
        loaded[branch] = rows
    root_reach = sum(row["reach"] for row in loaded["01_BB_FIRST"] if row["reach"] > 0)
    report = {}
    for model in ["separate-high-bdfd", "combined-high-bdfd", "all-bdfd"]:
        branches = {}
        total = 0.0
        for branch, meta in a.BRANCHES.items():
            result = a.analyze_branch(branch, meta, remap(loaded[branch], model))
            root_loss = (
                result["summary"]["weighted_loss_native"]
                / root_reach
                / a.EV_SCALE_PER_BB
            )
            total += root_loss
            branches[branch] = {
                "root_loss_bb": root_loss,
                "node_loss_bb": result["summary"]["mean_local_loss_bb"],
                "hand_categories": result["summary"]["hand_categories"],
                "populated_cells": result["summary"]["populated_cells"],
                "policy_cell_counts": result["summary"]["policy_cell_counts"],
            }
        report[model] = {"sum_root_loss_bb": total, "branches": branches}
    out = a.OUT_ROOT / "layered-comparison.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()

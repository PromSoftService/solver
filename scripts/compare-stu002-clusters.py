from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "analyze_stu002", REPO / "scripts" / "analyze-stu002.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load scripts/analyze-stu002.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

MADE = ["Two pair+", "Overpair", "Top pair", "Second pair", "Third pair", "Underpair", "Weak pair"]
UNMADE = ["2 overcards", "A-high", "Air"]


def remap(rows, made_to_merge=(), draw_to_merge=(), modes=None, all_base=False):
    result = []
    made_to_merge = set(made_to_merge)
    draw_to_merge = set(draw_to_merge)
    modes = modes or {}
    for source in rows:
        row = copy.copy(source)
        base = row["base"]
        if all_base or base in made_to_merge:
            row["hand_category"] = base
        elif base in draw_to_merge:
            has_draw = row["direct"] != "none" or row["bdfd"]
            row["hand_category"] = base + " + draw" if has_draw else base
        elif base in modes:
            mode = modes[base]
            if mode == "drop_bdfd":
                row["hand_category"] = (
                    base if row["direct"] == "none" else base + " + " + row["direct"]
                )
            elif mode == "direct_draw":
                row["hand_category"] = (
                    base if row["direct"] == "none" else base + " + draw"
                )
            else:
                raise ValueError(f"Unknown remap mode: {mode}")
        result.append(row)
    return result


def metric(branch, meta, rows, root_reach):
    out = a.analyze_branch(branch, meta, rows)["summary"]
    root_loss = out["weighted_loss_native"] / root_reach / a.EV_SCALE_PER_BB
    return {
        "hand_categories": out["hand_categories"],
        "populated_cells": out["populated_cells"],
        "node_loss_bb": out["mean_local_loss_bb"],
        "root_loss_bb": root_loss,
        "simplified_frequencies": out["simplified_reach_weighted_frequencies"],
    }


def main():
    loaded = {}
    for branch, meta in a.BRANCHES.items():
        rows, _, _ = a.read_branch(branch, meta)
        loaded[branch] = rows
    root_reach = sum(r["reach"] for r in loaded["01_BB_FIRST"] if r["reach"] > 0)
    report = {}
    for branch, meta in a.BRANCHES.items():
        rows = loaded[branch]
        strict = metric(branch, meta, rows, root_reach)
        cases = {"strict": strict}
        for base in MADE:
            cases["merge_" + base.replace(" ", "_")] = metric(
                branch, meta, remap(rows, made_to_merge=[base]), root_reach)
        for base in UNMADE:
            cases["draw_" + base.replace(" ", "_")] = metric(
                branch, meta, remap(rows, draw_to_merge=[base]), root_reach)
        for base in MADE + UNMADE:
            key = base.replace(" ", "_")
            cases["drop_bdfd_" + key] = metric(
                branch, meta, remap(rows, modes={base: "drop_bdfd"}), root_reach)
            cases["direct_draw_" + key] = metric(
                branch, meta, remap(rows, modes={base: "direct_draw"}), root_reach)
        cases["all_made"] = metric(branch, meta, remap(rows, made_to_merge=MADE), root_reach)
        cases["all_made_drop_bdfd"] = metric(
            branch, meta,
            remap(rows, modes={base: "drop_bdfd" for base in MADE}), root_reach)
        cases["strong_made"] = metric(
            branch, meta,
            remap(rows, made_to_merge=["Two pair+", "Overpair", "Top pair", "Underpair"]),
            root_reach)
        cases["strong_made_weak_direct"] = metric(
            branch, meta,
            remap(
                rows,
                made_to_merge=["Two pair+", "Overpair", "Top pair", "Underpair"],
                modes={base: "direct_draw" for base in ["Second pair", "Third pair", "Weak pair"]},
            ),
            root_reach)
        cases["practical"] = metric(
            branch, meta, remap(rows, made_to_merge=MADE, draw_to_merge=UNMADE), root_reach)
        cases["recommended_13"] = metric(
            branch,
            meta,
            remap(
                rows,
                made_to_merge=MADE,
                draw_to_merge=["2 overcards"],
                modes={"A-high": "direct_draw", "Air": "direct_draw"},
            ),
            root_reach,
        )
        cases["all_base"] = metric(branch, meta, remap(rows, all_base=True), root_reach)
        for value in cases.values():
            value["delta_root_loss_bb"] = value["root_loss_bb"] - strict["root_loss_bb"]
        report[branch] = cases
    out = a.OUT_ROOT / "cluster-comparison.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    compact = {}
    for branch, cases in report.items():
        compact[branch] = {
            name: {k: round(v, 8) if isinstance(v, float) else v for k, v in data.items()
                   if k in ("hand_categories", "populated_cells", "root_loss_bb", "delta_root_loss_bb")}
            for name, data in cases.items()
        }
    print(json.dumps(compact, ensure_ascii=False))


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


comparison = load_module(
    "compare_stu002_clusters", REPO / "scripts" / "compare-stu002-clusters.py"
)
analysis = comparison.a
OUTPUT = analysis.OUT_ROOT / "clustered-13"


def recommended_rows(rows: list[dict]) -> list[dict]:
    return comparison.remap(
        rows,
        made_to_merge=comparison.MADE,
        draw_to_merge=["2 overcards"],
        modes={"A-high": "direct_draw", "Air": "direct_draw"},
    )


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    loaded = {}
    for branch, meta in analysis.BRANCHES.items():
        rows, _, _ = analysis.read_branch(branch, meta)
        loaded[branch] = rows
    root_reach = sum(row["reach"] for row in loaded["01_BB_FIRST"] if row["reach"] > 0)

    manifest = {
        "model": "recommended-13",
        "pure_threshold": analysis.PURE_THRESHOLD,
        "mix_rule": "strict 50/50 top two actions",
        "categories": [
            "Two pair+", "Overpair", "Top pair", "Second pair", "Third pair",
            "Underpair", "Weak pair", "2 overcards", "2 overcards + draw",
            "A-high", "A-high + draw", "Air", "Air + draw",
        ],
        "branches": [],
    }
    for branch, meta in analysis.BRANCHES.items():
        strict = analysis.analyze_branch(branch, meta, loaded[branch])
        result = analysis.analyze_branch(branch, meta, recommended_rows(loaded[branch]))
        strict_root_loss = (
            strict["summary"]["weighted_loss_native"]
            / root_reach
            / analysis.EV_SCALE_PER_BB
        )
        root_loss = (
            result["summary"]["weighted_loss_native"]
            / root_reach
            / analysis.EV_SCALE_PER_BB
        )
        summary = dict(result["summary"])
        summary.update(
            model="recommended-13",
            strict_root_loss_bb=strict_root_loss,
            root_loss_bb=root_loss,
            incremental_root_loss_bb=root_loss - strict_root_loss,
        )

        branch_out = OUTPUT / branch
        write_csv(branch_out / "strategy.csv", result["matrix"], ["hand_category"] + analysis.B13)
        detail_fields = [
            "flop_class", "hand_category", "boards_present", "active_combos", "reach_sum",
        ] + [f"mean_{action}_frequency" for action in meta["actions"]]
        detail_fields += [
            "policy", "mean_frequency_distance", "mean_local_loss_bb", "max_combo_loss_bb",
        ]
        write_csv(branch_out / "cell-details.csv", result["details"], detail_fields)
        top_loss = sorted(
            result["details"], key=lambda row: row["mean_local_loss_bb"], reverse=True
        )[:10]
        write_csv(branch_out / "top-loss.csv", top_loss, detail_fields)
        (branch_out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest["branches"].append(
            {
                "branch": branch,
                "actor": meta["actor"],
                "action_shape": meta["shape"],
                "actions": meta["actions"],
                "labels": meta["labels"],
                "summary": summary,
            }
        )

    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()

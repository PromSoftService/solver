#!/usr/bin/env python
"""Audit the five-class human BB response to the STU002 UTG c-bet."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from flop_strategy import EV_SCALE_PER_BB, cards, flop_class, hand_category, rank

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "datasets" / "STU002__RNG001_UTG-vs-BB__BRD001_FLOP6" / "03_BB_AFTER_CBET" / "20260908-220332Z" / "combos.csv"
DEFAULT_OUTPUT = ROOT / "datasets" / "STU002__RNG001_UTG-vs-BB__BRD001_FLOP6" / "analysis" / "human-5" / "03_BB_AFTER_CBET"

FLOP_CLASSES = ["ABB", "Axx", "BBB", "Bxx", "[9-2]xx"]
HAND_ROWS = [
    "Two pair+", "Overpair", "Top pair", "Underpair", "Second pair",
    "Weak pair", "Third pair", "Low pocket pair", "OESD", "Gutshot",
    "2 overcards + BDFD", "Air",
]
PAIR_ROWS = set(HAND_ROWS[:8])
TABLE = {
    "Two pair+": ["C/R", "R/C", "C/R", "R", "R/C"],
    "Overpair": ["—", "—", "—", "C/R", "C"],
    "Top pair": ["C", "C", "BDFD", "C", "C/R"],
    "Underpair": ["—", "C", "—", "C", "C"],
    "Second pair": ["F", "C", "F", "C/R", "C"],
    "Weak pair": ["—", "F", "—", "C/F", "C"],
    "Third pair": ["F", "C/F", "F", "C", "C"],
    "Low pocket pair": ["F", "F", "F", "F", "F"],
    "OESD": ["R/C", "R", "C", "R/C", "R/C"],
    "Gutshot": ["C/F", "C", "C/F", "C/R", "C"],
    "2 overcards + BDFD": ["—", "—", "—", "C/R", "C/F"],
    "Air": ["F", "F", "F", "C/F", "C/F"],
}

SELECTORS = {
    "Top pair / BBB": "CALL with BDFD; otherwise FOLD.",
    "Weak pair / Bxx": "CALL when the flop has one Broadway card; FOLD when it has two.",
    "Third pair / Axx": "CALL on A + two low cards; on A + Broadway + low CALL only with BDFD.",
    "Gutshot / ABB": "CALL with any made pair inside the Gutshot; otherwise FOLD.",
    "Gutshot / BBB": "CALL with top, second or third pair inside the Gutshot; otherwise FOLD.",
    "2 overcards + BDFD / [9-2]xx": "CALL with Ax or two Broadway hole cards; otherwise FOLD.",
    "Air / Bxx and [9-2]xx": "CALL only AK; otherwise FOLD.",
}


def flop5(board: str) -> str:
    ranks = sorted((rank(card) for card in cards(board)), reverse=True)
    original = flop_class(board)
    if original == "ABB":
        return "ABB"
    if ranks[0] == 14:
        return "Axx"
    if original == "BBB":
        return "BBB"
    if ranks[0] >= 10:
        return "Bxx"
    return "[9-2]xx"


def classify_hand(board: str, combo: str) -> tuple[str, str, str, bool]:
    base, direct, bdfd, _ = hand_category(board, combo)
    if direct == "OESD":
        display = "OESD"
    elif direct == "Gutshot":
        display = "Gutshot"
    elif base in PAIR_ROWS:
        display = base
    elif base == "2 overcards" and bdfd:
        display = "2 overcards + BDFD"
    else:
        display = "Air"
    return display, base, direct, bool(bdfd)


def selector_calls(row: dict) -> bool:
    hand, fc = row["hand"], row["flop5"]
    if hand == "Weak pair" and fc == "Bxx":
        return row["broadway_count"] == 1
    if hand == "Third pair" and fc == "Axx":
        return row["broadway_count"] == 0 or row["bdfd"]
    if hand == "Gutshot" and fc == "ABB":
        return row["base"] in PAIR_ROWS
    if hand == "Gutshot" and fc == "BBB":
        return row["base"] in {"Top pair", "Second pair", "Third pair"}
    if hand == "2 overcards + BDFD" and fc == "[9-2]xx":
        return row["hole_high"] == 14 or row["hole_low"] >= 10
    if hand == "Air" and fc in {"Bxx", "[9-2]xx"}:
        return row["hole_high"] == 14 and row["hole_low"] == 13
    raise ValueError(f"No selector for {hand} / {fc}")


def policy(row: dict) -> tuple[float, float, float]:
    label = TABLE[row["hand"]][FLOP_CLASSES.index(row["flop5"])]
    if label == "F":
        return 1.0, 0.0, 0.0
    if label == "C":
        return 0.0, 1.0, 0.0
    if label == "R":
        return 0.0, 0.0, 1.0
    if label in {"C/R", "R/C"}:
        return 0.0, 0.5, 0.5
    if label == "BDFD":
        return (0.0, 1.0, 0.0) if row["bdfd"] else (1.0, 0.0, 0.0)
    if label == "C/F":
        return (0.0, 1.0, 0.0) if selector_calls(row) else (1.0, 0.0, 0.0)
    raise ValueError(f"Unsupported policy {label}")


def load_rows(path: Path) -> tuple[list[dict], float]:
    result = []
    max_mix_error = 0.0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            reach = float(raw["reach_probability"])
            if reach <= 0:
                continue
            board, combo = raw["board"], raw["combo"]
            hand, base, direct, bdfd = classify_hand(board, combo)
            board_ranks = sorted((rank(card) for card in cards(board)), reverse=True)
            hole_ranks = sorted((rank(card) for card in cards(combo)), reverse=True)
            solver = tuple(float(raw[name]) for name in ("fold_frequency", "call_frequency", "raise_frequency"))
            ev = tuple(float(raw[name]) for name in ("ev_fold", "ev_call", "ev_raise"))
            mixed = float(raw["mixed_ev"])
            max_mix_error = max(max_mix_error, abs(mixed - sum(p * q for p, q in zip(solver, ev))))
            row = {
                "board": board, "combo": combo, "reach": reach, "hand": hand,
                "base": base, "direct": direct, "bdfd": bdfd, "flop5": flop5(board),
                "broadway_count": sum(10 <= value <= 13 for value in board_ranks),
                "hole_high": hole_ranks[0], "hole_low": hole_ranks[1],
                "solver": solver, "ev": ev, "mixed": mixed,
            }
            row["candidate"] = policy(row)
            row["candidate_ev"] = sum(p * q for p, q in zip(row["candidate"], ev))
            row["best_ev"] = max(ev)
            result.append(row)
    return result, max_mix_error


def weighted_quantile(items: list[tuple[float, float]], quantile: float) -> float:
    ordered = sorted(items)
    target = sum(weight for _, weight in ordered) * quantile
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= target:
            return value
    return ordered[-1][0]


def summarize(rows: list[dict]) -> dict:
    total = sum(row["reach"] for row in rows)
    solver = [sum(row["reach"] * row["solver"][i] for row in rows) / total for i in range(3)]
    candidate = [sum(row["reach"] * row["candidate"][i] for row in rows) / total for i in range(3)]
    source_loss = sum(row["reach"] * (row["mixed"] - row["candidate_ev"]) for row in rows) / total / EV_SCALE_PER_BB
    oracle_loss = sum(row["reach"] * (row["best_ev"] - row["candidate_ev"]) for row in rows) / total / EV_SCALE_PER_BB
    regrets = [((row["best_ev"] - row["candidate_ev"]) / EV_SCALE_PER_BB, row["reach"]) for row in rows]
    result = {
        "row_count": len(rows), "total_reach": total,
        "solver_frequency_pct": dict(zip(("F", "C", "R"), (100 * value for value in solver))),
        "candidate_frequency_pct": dict(zip(("F", "C", "R"), (100 * value for value in candidate))),
        "frequency_delta_pp": dict(zip(("F", "C", "R"), (100 * (candidate[i] - solver[i]) for i in range(3)))),
        "mean_source_loss_bb": source_loss, "mean_oracle_regret_bb": oracle_loss,
        "p95_oracle_regret_bb": weighted_quantile(regrets, 0.95),
        "p99_oracle_regret_bb": weighted_quantile(regrets, 0.99),
        "p999_oracle_regret_bb": weighted_quantile(regrets, 0.999),
        "max_oracle_regret_bb": max(value for value, _ in regrets),
    }
    result["overcall_loss_bb"] = sum(
        row["reach"] * row["candidate"][1] * max(row["ev"][0] - row["ev"][1], 0)
        for row in rows) / total / EV_SCALE_PER_BB
    result["overfold_loss_bb"] = sum(
        row["reach"] * row["candidate"][0] * max(row["ev"][1] - row["ev"][0], 0)
        for row in rows) / total / EV_SCALE_PER_BB
    result["bad_raise_loss_bb"] = sum(
        row["reach"] * row["candidate"][2] * max(max(row["ev"][:2]) - row["ev"][2], 0)
        for row in rows) / total / EV_SCALE_PER_BB
    result["missed_raise_loss_bb"] = sum(
        row["reach"] * (1 - row["candidate"][2]) * max(row["ev"][2] - max(row["ev"][:2]), 0)
        for row in rows) / total / EV_SCALE_PER_BB
    return result


def cell_records(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["hand"], row["flop5"])].append(row)
    records = []
    for hand in HAND_ROWS:
        for fc in FLOP_CLASSES:
            group = groups.get((hand, fc))
            if not group:
                continue
            total = sum(row["reach"] for row in group)
            entry = {"hand": hand, "flop5": fc, "reach": total}
            for i, action in enumerate(("F", "C", "R")):
                entry[f"solver_{action}_pct"] = 100 * sum(row["reach"] * row["solver"][i] for row in group) / total
                entry[f"candidate_{action}_pct"] = 100 * sum(row["reach"] * row["candidate"][i] for row in group) / total
            entry["source_loss_bb"] = sum(
                row["reach"] * (row["mixed"] - row["candidate_ev"]) for row in group
            ) / total / EV_SCALE_PER_BB
            entry["oracle_regret_bb"] = sum(
                row["reach"] * (row["best_ev"] - row["candidate_ev"]) for row in group
            ) / total / EV_SCALE_PER_BB
            regrets = [((row["best_ev"] - row["candidate_ev"]) / EV_SCALE_PER_BB, row["reach"]) for row in group]
            entry["p99_oracle_regret_bb"] = weighted_quantile(regrets, 0.99)
            entry["max_oracle_regret_bb"] = max(value for value, _ in regrets)
            records.append(entry)
    return records

def selector_records(rows: list[dict]) -> list[dict]:
    targets = {
        ("Top pair", "BBB"): SELECTORS["Top pair / BBB"],
        ("Weak pair", "Bxx"): SELECTORS["Weak pair / Bxx"],
        ("Third pair", "Axx"): SELECTORS["Third pair / Axx"],
        ("Gutshot", "ABB"): SELECTORS["Gutshot / ABB"],
        ("Gutshot", "BBB"): SELECTORS["Gutshot / BBB"],
        ("2 overcards + BDFD", "[9-2]xx"): SELECTORS["2 overcards + BDFD / [9-2]xx"],
        ("Air", "Bxx"): SELECTORS["Air / Bxx and [9-2]xx"],
        ("Air", "[9-2]xx"): SELECTORS["Air / Bxx and [9-2]xx"],
    }
    records = []
    for (hand, fc), rule in targets.items():
        whole = [row for row in rows if row["hand"] == hand and row["flop5"] == fc]
        whole_reach = sum(row["reach"] for row in whole)
        for action, index in (("FOLD", 0), ("CALL", 1)):
            group = [row for row in whole if row["candidate"][index] == 1.0]
            reach = sum(row["reach"] for row in group)
            record = {
                "hand": hand, "flop5": fc, "rule": rule, "selected_action": action,
                "row_count": len(group), "reach": reach,
                "reach_share_pct": 100 * reach / whole_reach,
            }
            for i, name in enumerate(("F", "C", "R")):
                record[f"solver_{name}_pct"] = 100 * sum(
                    row["reach"] * row["solver"][i] for row in group
                ) / reach
            record["mean_call_minus_fold_bb"] = sum(
                row["reach"] * (row["ev"][1] - row["ev"][0]) for row in group
            ) / reach / EV_SCALE_PER_BB
            records.append(record)
    return records


def composition(rows: list[dict]) -> dict:
    answer = {}
    for action, index in (("CALL", 1), ("RAISE", 2)):
        solver = []
        candidate = []
        for hand in HAND_ROWS:
            group = [row for row in rows if row["hand"] == hand]
            solver.append(sum(row["reach"] * row["solver"][index] for row in group))
            candidate.append(sum(row["reach"] * row["candidate"][index] for row in group))
        solver_total, candidate_total = sum(solver), sum(candidate)
        solver_share = [value / solver_total for value in solver]
        candidate_share = [value / candidate_total for value in candidate]
        answer[action] = {
            "total_variation": 0.5 * sum(abs(a - b) for a, b in zip(solver_share, candidate_share)),
            "by_hand": [
                {"hand": hand, "solver_share_pct": 100 * solver_share[i],
                 "candidate_share_pct": 100 * candidate_share[i],
                 "delta_pp": 100 * (candidate_share[i] - solver_share[i])}
                for i, hand in enumerate(HAND_ROWS)
            ],
        }
    return answer


def write_csv(path: Path, records: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def write_outputs(output: Path, rows: list[dict], max_mix_error: float) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    metrics = summarize(rows)
    cells = cell_records(rows)
    board_counts = {fc: len({row["board"] for row in rows if row["flop5"] == fc}) for fc in FLOP_CLASSES}
    audit = {
        "scope": "STU002 03_BB_AFTER_CBET; 286 unpaired rainbow flops; native raise to 9.5 bb",
        "flop_classes": board_counts, "max_mixed_ev_reproduction_error": max_mix_error,
        "metrics": metrics, "composition": composition(rows),
    }
    (output / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output / "cell-audit.csv", cells)
    write_csv(output / "selector-audit.csv", selector_records(rows))
    with (output / "strategy.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["hand", *FLOP_CLASSES])
        for hand in HAND_ROWS:
            writer.writerow([hand, *TABLE[hand]])
    candidate = {
        "status": "locally EV-audited human candidate; not a re-solve or exploitability proof",
        "classes": {
            "ABB": "Ace-high with two Broadway cards", "Axx": "other Ace-high flops",
            "BBB": "three Broadway cards", "Bxx": "K/Q/J/T-high excluding BBB",
            "[9-2]xx": "highest card 9 or lower",
        },
        "table": TABLE, "selectors": SELECTORS, "audit": metrics,
    }
    (output / "candidate.json").write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    worst = sorted(rows, key=lambda row: row["best_ev"] - row["candidate_ev"], reverse=True)[:50]
    write_csv(output / "worst-combos.csv", [
        {
            "board": row["board"], "combo": row["combo"], "flop5": row["flop5"],
            "hand": row["hand"], "base": row["base"], "bdfd": row["bdfd"],
            "candidate_F": row["candidate"][0], "candidate_C": row["candidate"][1],
            "candidate_R": row["candidate"][2],
            "source_loss_bb": (row["mixed"] - row["candidate_ev"]) / EV_SCALE_PER_BB,
            "oracle_regret_bb": (row["best_ev"] - row["candidate_ev"]) / EV_SCALE_PER_BB,
        }
        for row in worst
    ])
    return audit


def write_readme(output: Path, audit: dict) -> None:
    m = audit["metrics"]
    lines = [
        "# STU002 BB response: five-class human candidate", "",
        "This is a separate, locally EV-audited candidate. It does not replace the canonical",
        "ten-class workbook and is not a re-solve or an exploitability proof.", "",
        "| Hand category | " + " | ".join(FLOP_CLASSES) + " |",
        "|---|" + "|".join("---:" for _ in FLOP_CLASSES) + "|",
    ]
    for hand in HAND_ROWS:
        lines.append("| " + hand + " | " + " | ".join(TABLE[hand]) + " |")
    lines.extend(["", "## Selectors", ""])
    for cell, rule in SELECTORS.items():
        lines.append(f"- **{cell}:** {rule}")
    lines.extend([
        "", "## Audit summary", "",
        f"- Solver F/C/R: {m['solver_frequency_pct']['F']:.2f}% / {m['solver_frequency_pct']['C']:.2f}% / {m['solver_frequency_pct']['R']:.2f}%.",
        f"- Candidate F/C/R: {m['candidate_frequency_pct']['F']:.2f}% / {m['candidate_frequency_pct']['C']:.2f}% / {m['candidate_frequency_pct']['R']:.2f}%.",
        f"- Mean loss versus source mix: {m['mean_source_loss_bb']:.6f} bb.",
        f"- Mean oracle regret: {m['mean_oracle_regret_bb']:.6f} bb.",
        f"- Weighted P95 / P99: {m['p95_oracle_regret_bb']:.6f} / {m['p99_oracle_regret_bb']:.6f} bb.",
        "", "`C/R` and `R/C` are the same exact 50/50 randomizer; order records solver majority.",
        "`C/F` is deterministic and uses the stated selector, never a randomizer.", "",
    ])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows, max_mix_error = load_rows(args.input)
    audit = write_outputs(args.output, rows, max_mix_error)
    write_readme(args.output, audit)
    expected = {"ABB": 6, "Axx": 60, "BBB": 4, "Bxx": 160, "[9-2]xx": 56}
    if audit["flop_classes"] != expected:
        raise SystemExit(f"Unexpected class counts: {audit['flop_classes']}")
    if max_mix_error > 1e-9:
        raise SystemExit(f"mixed_ev reproduction failed: {max_mix_error}")
    print(json.dumps(audit["metrics"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

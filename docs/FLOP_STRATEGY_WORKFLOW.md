# Standard workflow for human flop strategies

This document is the repository contract for producing the approved human
flop tables. Remote `main` is the source of truth. Do not reconstruct this
method from chat memory or from already simplified action labels.

## 1. Current studies and scope

| Study | Spot | Pot / stack on flop | Jobs |
|---|---|---|---:|
| `STU002__RNG001_UTG-vs-BB__BRD001_FLOP6` | UTG open 2.5 bb, BB call; OOP BB, IP UTG | 5.5 / 97.5 bb | 6 |
| `STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4` | UTG open 2.5 bb, BTN call; OOP UTG, IP BTN | 6.5 / 97.5 bb | 4 |

Each job covers all 286 BRD001 flops. It solves a full continuation game but
exports and analyzes one configured flop decision only. Turn and river remain
in the tree so flop EVs have a valid continuation; they are not current study
outputs.

Every completed study publishes two workbooks:

1. `<STU>_simplified_flop_strategy.xlsx`: 12 hand rows by 13 B13 categories;
2. `<STU>_strategy_8_categories.xlsx`: the same rows by eight broad categories.

Every cell is one pure action or an exact 50/50 mix.

## 2. Range provenance

The canonical manifests and concrete files under `ranges/` are the only range
source. Both matched preflop solutions came from the range library bundled
with TexasSolverGPU v0.2.0, not GTO Wizard:

| Range | Spot | Bundled source path |
|---|---|---|
| RNG001 | UTG open 2.5 bb / BB call | `ranges/6max_range/UTG/2.5bb/BB/Call` |
| RNG002 | UTG open 2.5 bb / BTN call | `ranges/6max_range/UTG/2.5bb/BTN/Call` |

The manifests retain source SHA-256 values and weighted-combo totals. Study
configs contain the corresponding exact 1326-combo arrays. A combo with any
positive source weight belongs to the range, even if its weight is tiny.

## 3. Solver abstraction and selected decisions

| Street | OOP bet/donk | IP bet | Raise |
|---|---:|---:|---:|
| Flop | 50% | 50% | 60 native TexasSolver |
| Turn continuation | 50% | 50% | 60 native TexasSolver |
| River continuation | 75% | 100% | 60 native TexasSolver |

There is one normal raise after the opening bet. TexasSolver counts the
opening bet in `maxRaiseNumber`, so the native value is `2`. The proven v015
all-in semantics remain unchanged: all-in is enabled for both players on every
street with `addAllinThreshold=200`.

STU002 exports six UTG-vs-BB decisions:

| Branch | Selected decision | Normal actions |
|---|---|---|
| `01_BB_FIRST` | BB at flop root | check / donk 50% |
| `02_UTG_AFTER_CHECK` | UTG after BB check | check / bet 50% |
| `03_BB_AFTER_CBET` | BB versus UTG c-bet | fold / call / raise 60 |
| `04_UTG_AFTER_CHECK_RAISE` | UTG versus check-raise | fold / call |
| `05_UTG_AFTER_DONK` | UTG versus BB donk | fold / call / raise 60 |
| `06_BB_AFTER_DONK_RAISE` | BB versus raise after donk | fold / call |

STU004 exports four UTG-vs-BTN decisions:

| Branch | Selected decision | Normal actions |
|---|---|---|
| `01_UTG_FIRST` | UTG at flop root | check / bet 50% |
| `02_BTN_AFTER_CHECK` | BTN after UTG check | check / bet 50% |
| `03_BTN_AFTER_CBET` | BTN versus UTG c-bet | fold / call / raise 60 |
| `04_UTG_AFTER_STAB` | UTG versus BTN stab | fold / call / raise 60 |

STU004 deliberately omits the two responses after a flop raise. Those require
a separately approved study if needed.

For every board and branch the stock runner performs exactly one GPU solve,
applies one configured history, and calls `solver.export.currentStreet` once.
No exhaustive full-tree traversal or guessed API is allowed. `-Resume` reuses
completed board directories and retries only missing or failed boards.

## 4. Persistence and validation

Raw node files stay under ignored `output/`. Approved compact evidence is
stored under `datasets/<study>/...` and contains branch summaries, validation,
timing, aggregate `combos.csv`, and provenance notes.

A branch is complete only when it has:

- 286 done and zero failed boards;
- 286 PASS validation rows;
- the exact expected `combos.csv` header and row count;
- exactly one `solver.solve.start` and one
  `solver.export.currentStreet` per board;
- zero forbidden full-tree calls.

Once compact evidence is complete, rebuilding either strategy table requires
no new GPU solve.

## 5. Flop categories

BRD001 contains 286 canonical unpaired rainbow flops. B13 is mutually
exclusive and exhaustive:

| B13 | Count |
|---|---:|
| ABB | 6 |
| A[K/Q]x | 16 |
| A[J-T][9-5] | 10 |
| A[J-T][4-2] | 6 |
| A[9-7]x | 18 |
| A[6-2]x | 10 |
| BBB | 4 |
| BBx | 47 |
| K/Qx dis | 42 |
| K/Qx con | 14 |
| [J-8]x dis | 67 |
| [J-8]x con | 26 |
| [7-4]x | 20 |

`B` means T/J/Q/K; ace is separate. For `con`, the two lower ranks are
adjacent. `JT9` belongs to `[J-8]x con`, not BBx.

| Final group | B13 members | Count |
|---|---|---:|
| A-high high | ABB + A[K/Q]x | 22 |
| A-high medium | A[J-T][9-5] + A[J-T][4-2] | 16 |
| A-high low | A[9-7]x + A[6-2]x | 28 |
| Broadway | BBB + BBx | 51 |
| K/Q-high | K/Qx dis + K/Qx con | 56 |
| Middle dry | [J-8]x dis | 67 |
| Middle connected | [J-8]x con | 26 |
| Low | [7-4]x | 20 |

The broad table is recomputed from real board/combo frequencies. It never
averages B13 means or votes on B13 labels; each real board has equal influence
inside its broad group.

## 6. Strict hand classifier and displayed rows

Every legal combo receives exactly one made-hand base. In display order these
are Two pair+, Overpair, Top pair, Underpair, Second pair, Weak pair, Third
pair, Low pocket pair, 2 overcards, A-high, and Air. `Two pair+` includes made
straights. `Underpair` is a pocket pair strictly between the top and middle
flop ranks. `Weak pair` is a pocket pair strictly between the middle and low
flop ranks. `Low pocket pair` is a pocket pair below the low flop rank.

The classifier also assigns exactly one direct-draw state (`none`, `Gutshot`,
or `OESD`) and one BDFD boolean. Double gutshots count as OESD. On a rainbow
flop, BDFD requires suited hole cards plus one flop card of that suit.

The strict result is mapped to these 12 learnable rows, in display order:

1. Two pair+
2. Overpair
3. Top pair
4. Underpair
5. Second pair
6. Weak pair
7. Third pair
8. Low pocket pair
9. OESD
10. Gutshot
11. 2 overcards + BDFD
12. Air

Made-hand variants merge into their base regardless of draw modifiers. Every
remaining unmade hand follows this priority: OESD; otherwise Gutshot;
otherwise exactly two overcards plus BDFD; otherwise Air. Naked overcards,
A-high, A-high plus BDFD, and Air plus BDFD therefore belong to Air.

## 7. From solver frequencies to one cell

The policy is always rebuilt from numeric action frequencies in tracked
`combos.csv`. Never infer frequencies from an existing label.

For one branch, hand row, and target flop category:

1. Exclude only rows with `reach_probability <= 0` at the selected node.
2. On each board, take the ordinary mean of action frequencies over all
   participating concrete combos in the row. Do not weight this policy mean by
   source weight or reach magnitude.
3. Take the ordinary mean of those board means across all real boards on which
   the row is present. Every board has equal weight.
4. If the largest action mean is strictly greater than 65%, choose it pure.
5. Otherwise choose the two most frequent actions as an exact 50/50 mix. In
   the displayed label, put the more frequent solver action first (`C/R`
   means call was more frequent than raise). If their means are exactly tied,
   use the fixed native action order.
6. If no combo is present for that range/node/category, display `—`.

The B13 and broad tables run this independently from the same raw solver
frequencies. Three-way and non-50/50 mixes are prohibited. The discussed
three-percentage-point EV tie-break remains deferred.

## 8. EV audit

EV does not choose the displayed action. After frequency selection, every
concrete combo is audited against the solved opponent:

```text
local_regret = max(0, solver_mixed_ev - simplified_policy_ev)
```

Loss aggregates are weighted by `reach_probability`; native EV is divided by
ten to report big blinds. This is reach-weighted local regret, not adaptive
exploitability against an opponent who re-solves after seeing the policy.

## 9. Rebuilding the two outputs

From repository root:

```text
python scripts/generate-flop-strategies.py <study-directory> [--run <run-name>]
node scripts/build-flop-workbooks.mjs <study-directory>
```

Examples:

```text
python scripts/generate-flop-strategies.py STU002__RNG001_UTG-vs-BB__BRD001_FLOP6
node scripts/build-flop-workbooks.mjs STU002__RNG001_UTG-vs-BB__BRD001_FLOP6

python scripts/generate-flop-strategies.py STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4 --run run-20260909-221703Z
node scripts/build-flop-workbooks.mjs STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4
```

The numeric generator validates inputs, board partitions, player support, and
classification, then writes `strategy-13`, `strategy-8`, and final validation
artifacts. The workbook builder writes both `.xlsx` files with the approved
action colors. Both workbooks must be recalculated, scanned for formula errors,
rendered, and visually checked after regeneration.

## 10. Non-goals

- Do not restore discarded row-smoothing experiments.
- Do not derive frequencies from a simplified table.
- Do not add bet sizes without a new study decision.
- Do not analyze turn or river yet.
- Do not call local regret exploitability.
- Do not replace canonical ranges or solver inputs with remembered values.

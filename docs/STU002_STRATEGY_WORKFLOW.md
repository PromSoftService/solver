# STU002: standard workflow for the human flop strategy

This document is the handoff contract for continuing STU002 in a new chat.
Remote `main` is the source of truth; do not reconstruct the method from chat
memory when the repository can be read.

## 1. Goal and current scope

STU002 builds a learnable UTG-versus-BB flop strategy for the spot:

- 6-max NLHE cash, 100 bb;
- UTG opens 2.5 bb and BB calls;
- OOP is BB and IP is UTG;
- flop pot is 5.5 bb (`startingPot=55` in native tenths of a blind);
- effective flop stack is 97.5 bb (`effectiveStack=975`).

The deliverable is six tables, one for every normal-action decision on the
flop.  Each cell contains one pure action or an exact 50/50 mix.  We publish
the same strategy in two resolutions:

1. `STU002_simplified_flop_strategy.xlsx`: 13 hand rows by the 13 B13 flop
   categories;
2. `STU002_strategy_8_categories.xlsx`: the same 13 hand rows by eight broader
   flop categories.

Turn and river are deliberately outside the current strategy analysis.  They
remain in the solver tree as continuation abstractions because flop EVs need a
valid continuation game, but STU002 exports and analyzes only the selected
flop decision.

## 2. Range provenance

The range ID is `RNG001`.  Its canonical manifest is:

`ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1.json`

The concrete source files are:

- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__UTG.txt`;
- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__BB.txt`.

They came from the range library bundled with TexasSolverGPU v0.2.0, path
`ranges/6max_range/UTG/2.5bb/BB/Call`.  They are not GTO Wizard ranges.  The
manifest stores the source-file SHA-256 values.  `config.json` contains the
corresponding exact 1326-combo arrays: IP is UTG and OOP is BB.  CI compares
the STU002 arrays with the proven RNG001 input so an accidental range change
fails before a study is run.

A combo with a positive source weight belongs to the range even if its weight
is very small.  Strategy aggregation therefore does not delete a 0.01%-type
combo merely because it is rare.

## 3. Solver abstraction and six independent jobs

The active study package is:

`studies/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/`

Normal sizes:

| Street | OOP bet/donk | IP bet | Raise |
|---|---:|---:|---:|
| Flop | 50% | 50% | 60 native TexasSolver |
| Turn continuation | 50% | 50% | 60 native TexasSolver |
| River continuation | 75% | 100% | 60 native TexasSolver |

There is one normal raise after the opening bet.  TexasSolver counts the
opening bet in `maxRaiseNumber`, so the native value is `2`.  The proven v015
all-in semantics remain unchanged: all-in is enabled for both players on every
street and `addAllinThreshold=200`.  Do not invent a new all-in threshold.

The stock bridge exports one selected current-street decision.  Therefore the
complete flop interaction is six independent jobs, not one reusable saved
tree:

| Branch | Acting player and selected history | Available normal actions |
|---|---|---|
| `01_BB_FIRST` | BB at the flop root | check / donk 50% |
| `02_UTG_AFTER_CHECK` | UTG after BB checks | check / bet 50% |
| `03_BB_AFTER_CBET` | BB after check, UTG bet 50% | fold / call / raise 60 |
| `04_UTG_AFTER_CHECK_RAISE` | UTG after BB check-raises | fold / call |
| `05_UTG_AFTER_DONK` | UTG after BB donks 50% | fold / call / raise 60 |
| `06_BB_AFTER_DONK_RAISE` | BB after UTG raises the donk | fold / call |

For every board and every branch the runner performs exactly one GPU solve,
applies exactly one configured history, and calls
`solver.export.currentStreet` exactly once.  No exhaustive full-tree traversal,
guessed API or reloadable full-tree archive is part of this study.

Run one branch:

```powershell
.\studies\STU002__RNG001_UTG-vs-BB__BRD001_FLOP6\run-branch.ps1 -BranchId 01_BB_FIRST
```

Run all six sequentially:

```powershell
.\studies\STU002__RNG001_UTG-vs-BB__BRD001_FLOP6\run-all.ps1
```

`-Resume` is allowed only with the unchanged config and the same output
directory.  It reuses completed board directories and retries only missing or
failed boards.

## 4. What is persisted and validated

Raw node files stay under ignored `output/`.  After a branch reaches 286/286,
`run-branch.ps1` validates every board and writes the approved compact dataset
under `datasets/STU002.../<branch>/<UTC timestamp>/`.

The compact evidence for every branch contains:

- `batch-summary.json` and `.csv`;
- `validation.csv`;
- `timing-report.json`;
- one aggregate `combos.csv` assembled from canonical per-board
  `combos.json` files;
- a short `README.md`.

Required validation is 286 done, zero failed, correct CSV header and combo
count, exactly one `solver.solve.start`, exactly one
`solver.export.currentStreet`, and zero forbidden full-tree calls per board.
The six completed compact datasets in `main` are the source for all current
strategy tables.  No new GPU solve is needed to rebuild the tables.

## 5. Flop classification

BRD001 contains 286 canonical unpaired rainbow flops.  B13 is mutually
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

`B` means T/J/Q/K; A is separate.  For the `con`/`dis` split the two lower
ranks are adjacent when `middle_rank - low_rank = 1`.  `JT9` belongs to
`[J-8]x con`, not BBx.  This is why the final counts are BBx=47 and
`[J-8]x con`=26.

The eight broader categories are also mutually exclusive and exhaustive:

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

For the eight-column table these eight groups are the actual categories.  B13
is only the deterministic membership rule.  Every real board contributes
equally inside its final group; we do not average the already aggregated B13
means.  Consequently 47 BBx boards naturally carry more influence than four
BBB boards inside Broadway.

## 6. Strict combo classifier and the 13 displayed hand rows

Every legal concrete hand on every flop receives exactly one base category by
this priority:

1. Two pair+;
2. Overpair;
3. Top pair;
4. Second pair;
5. Third pair;
6. Underpair;
7. Weak pair;
8. 2 overcards;
9. A-high;
10. Air.

`Two pair+` includes made straights.  `Underpair` is a pocket pair strictly
between the top and middle flop ranks.  `Weak pair` is a lower pocket pair.

The classifier also assigns exactly one direct-draw state (`none`, `Gutshot`
or `OESD`) and one BDFD boolean.  Double gutshots count as OESD.  On rainbow
flops BDFD requires suited hole cards plus one flop card of that suit.  A made
straight receives no direct-draw modifier.

The strict classifier is then mapped to 13 learnable rows:

1. Two pair+
2. Overpair
3. Top pair
4. Underpair
5. Second pair
6. Third pair
7. Weak pair
8. 2 overcards
9. 2 overcards + draw
10. A-high
11. A-high + draw
12. Air
13. Air + draw

For every made-hand base, all BDFD/Gutshot/OESD variants merge into the base.
For `2 overcards`, `+ draw` means BDFD or a direct straight draw.  For A-high
and Air, `+ draw` means a direct Gutshot/OESD only; a lone BDFD stays in the
naked row.  This asymmetric rule was chosen from the source solver data and
avoids the large error caused by treating every BDFD as equivalent to a direct
straight draw.

The order above is the display order.  Moving Underpair directly below Top
pair is a presentation change only; it does not alter classification.

## 7. From source solver frequencies to one cell

The policy is always rebuilt from the numeric action frequencies in the six
aggregate `combos.csv` datasets.  Never translate existing labels such as
`F/C` back into invented frequencies.

For one branch, hand row and final flop category:

1. Discard only combo rows with `reach_probability <= 0` at that selected
   node.  A combo with any positive reach participates.
2. On each individual board, take the ordinary arithmetic mean of the solver
   action frequencies across all participating concrete combos in the hand
   row.  Do not weight this policy-selection mean by source range weight or by
   the magnitude of reach.
3. Take the ordinary arithmetic mean of those board-level means across every
   real board on which the row is present in the flop category.  Every board
   has equal weight.
4. Rank actions by the resulting means.  If the largest mean is strictly
   greater than 65%, choose that action pure.
5. Otherwise choose the two most frequent actions as an exact 50/50 mix.
   Three-way mixes and non-50/50 mixes are prohibited.
6. If the category has no participating combo in that range/node, display
   `—`.

This same algorithm is run separately for the B13 and eight-category tables.
The eight-category table is not produced by merging or voting on the displayed
B13 labels; it is recalculated from the original solver combo frequencies.

The previously discussed three-percentage-point EV tie-break is deferred.  It
is not part of the current standard and must not silently appear in either
workbook.

## 8. EV audit

EV does not select the displayed action in the current version.  After the
frequency policy is fixed, each concrete combo is audited against the solved
opponent:

```text
local_regret = max(0, solver_mixed_ev - simplified_policy_ev)
```

`simplified_policy_ev` uses the pure action or exact 50/50 action pair chosen
for its cell.  Loss aggregates are weighted by `reach_probability` and native
EV is divided by ten to report big blinds.  The result is reach-weighted local
regret, not adaptive exploitability against an opponent who re-solves after
seeing the simplification.

EV remains useful for comparison and risk auditing, especially where a broad
category mixes fold with continue/raise behavior, but it is not a hidden
action selector.

## 9. Rebuilding the approved outputs

From repository root, with Python available:

```text
python scripts/generate-stu002-strategies.py
```

This validates the six compact datasets, all board partitions, player combo
support and strict classification, then creates:

- `analysis/strategy-13/`;
- `analysis/strategy-8/`;
- `analysis/FINAL_VALIDATION.json`;
- `analysis/FLOP_GROUPS.json`.

The workbook builder is:

```text
node scripts/build-stu002-workbooks.mjs
```

It uses `@oai/artifact-tool` and writes the two approved `.xlsx` files at the
analysis root.  The workbooks contain Summary, the six decisions, and Method.
All action cells are data values rather than formulas.  The final files must be
rendered and visually checked after regeneration.

## 10. Current non-goals

- Do not restore the discarded row-smoothing experiments.
- Do not infer frequencies from an already simplified table.
- Do not add more bet sizes to STU002 without a new study decision.
- Do not analyze turn or river yet.
- Do not call the result exploitability.
- Do not replace the TexasSolverGPU ranges or solver with remembered values
  from another chat.

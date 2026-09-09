# STU002 layered-smooth-12

This is the first human-readable flop strategy for `RNG001` (UTG open 2.5bb,
BB call) over all 286 `BRD001` flops and all six STU002 flop decisions.

## Hand hierarchy

Every in-range combo on every flop maps to exactly one of these categories,
in this priority order:

1. `Two pair+`
2. `Overpair`
3. `Top pair`
4. `Second pair`
5. `Third pair`
6. `Underpair`
7. `Weak pair`
8. `OESD`
9. `Gutshot`
10. `2 overcards + BDFD`
11. `A-high + BDFD`
12. `Air`

For the seven made-hand categories, straight-draw and BDFD modifiers are
absorbed into the made hand. For unmade hands, OESD has priority over
Gutshot. The two BDFD categories contain only hands without a direct
straight draw. `Air` is last and combines the remaining plain two-overcard,
A-high, and air hands.

Double-gutshot is classified as `OESD`.

## Aggregation and initial policy

- Include every combo with `reach_probability > 0`, regardless of the size
  of its preflop weight.
- On each board/category, average combo action frequencies equally.
- Inside each B13 flop class, average the board values equally.
- If the largest mean action frequency is above 65%, use that pure action.
- Otherwise use the two largest actions as a strict 50/50 mix.

## Row smoothing

The fixed left-to-right B13 order is retained. Each hand-category row is
restricted to at most three contiguous action blocks. A block is either a
pure action or a strict 50/50 mix; no other mixing frequencies are allowed.

For a given structural complexity, actions are selected by proximity to the
solver frequencies, not by maximizing the displayed EV. EV is used only to
decide whether the added simplification is acceptable.

Per branch, smoothing is capped by both:

- `0.001 bb` additional loss measured from the root;
- `0.01 bb` additional loss conditional on reaching that decision node.

## Loss audit

All loss values are reach-weighted local regret against the solved opponent.
They are not adaptive exploitability.

- Unsmoothed 12-category model: `0.0162928763 bb` from root = `1.6293 bb/100`.
- Smoothed model: `0.0191555443 bb` from root = `1.9156 bb/100`.
- Increment caused by row smoothing: `0.0028626680 bb` = `0.2863 bb/100`.

The workbook `STU002_strategy_layered_smooth_12.xlsx` contains the six final
tables, summary metrics, the action legend, the B13 definitions, and this
methodology in a compact form.

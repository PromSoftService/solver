# STU002 clustered-13 smooth v2

Source: accepted `analysis/clustered-13` strategy. Hand and flop categories are unchanged.

## Why v1 smoothing failed

The previous `layered-smooth-12` optimizer minimized EV loss under a broad branch cap. Near-indifferent solver actions could therefore be replaced wholesale: BB donks disappeared and UTG raises versus donk expanded from about 6% to about 20%. It is retained only as an audit trail and is superseded by this directory.

## v2 rule

- A block is a contiguous run of the same pure action or the same strict 50/50 mix in fixed B13 order.
- Rows already containing at most three blocks are unchanged.
- Noisy rows are simplified with dynamic programming toward at most three blocks.
- Pure actions are anchors: changing a pure cell is penalized before changing a boundary mix.
- B13 columns are weighted by the number of boards in the class.
- Global reach-weighted action-frequency drift is capped at 1.5 percentage points per branch.
- Reach-weighted action-frequency drift inside any B13 class is capped at 15 percentage points.
- Incremental reach-weighted local-regret loss is capped at 0.00025 bb from root per branch.
- If three blocks violate a guard, more blocks are restored. Strategic fidelity has priority over forced visual simplicity.
- EV is an audit guard only; it does not select the action.
- All mixed cells remain exactly 50/50.

## Critical checks

- BB first: donk/mix on `[7-4]x` is preserved.
- UTG versus BB donk: simplified raise frequency changes only from 6.01% to 5.99%.
- BB versus raise after donk, Second pair: `C C F F F F C C C C C C C`.

See `manifest.json` for branch metrics and each branch's `row-audit.csv` for row-level changes.

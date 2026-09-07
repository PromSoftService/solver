# RNG002 / CFG003 / NOD006 — UTG defense versus BTN stab

Dataset: `datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-20260907-192002.csv`.

Spot: 6-max, 100bb, UTG open 2.5bb, BTN call, flop UTG checks, BTN bets 33%, UTG responds Fold / Call / Raise 60%. Board set: 286 unpaired rainbow flops (`BRD001`). All aggregates and local-regret values are weighted by `reach_probability`.

`local regret` is the EV loss against the equilibrium opponent strategy in the solved tree. It is not exploitability after opponent adaptation; no strategy-lock / best-response validation has been run.

## Solver structure

The familiar six flop classes collapse naturally into three defense classes:

| Flop class | Solver F / C / R |
|---|---:|
| **A[K-J]x** | **22.0 / 76.1 / 1.9** |
| **A[T-2]x + BBx** | **27.3 / 67.2 / 5.5** |
| **K-low** = K[9-2]x + [Q-8]x + [7-4]x | **30.4 / 51.6 / 18.0** |
| **Overall** | **29.6 / 55.2 / 15.2** |

This is a clean monotonic progression: high ace-heavy boards are almost pure call after filtering weak hands, the middle class has a small raise component, and K-low boards need materially more raising.

## Preferred human strategy

### 1. A[K-J]x

FOLD:
- Air / Nothing
- bare BDFD (`0OC`)
- Underpair `99-`

CALL:
- everything else

RAISE:
- none

Result: candidate **26.7 / 73.3 / 0.0** versus solver **22.0 / 76.1 / 1.9**. Local regret: **0.0057bb**.

### 2. A[T-2]x + BBx

FOLD:
- Air / Nothing
- X-high + `1OC`
- BDFD with `0OC` or `1OC`

RAISE:
- Two pair+ -> RAISE 100%

CALL:
- everything else

Result: candidate **28.6 / 67.5 / 3.9** versus solver **27.3 / 67.2 / 5.5**. Local regret: **0.0129bb**.

A slightly lower-regret variant also raises OESD, but the gain is negligible (~0.00002bb in this class) while adding another rule. Two pair+ only is therefore preferred.

### 3. K-low = K[9-2]x + [Q-8]x + [7-4]x

FOLD:
- Air / Nothing
- X-high + `1OC`
- X-high + `2OC` -> FOLD 75% / CALL 25%

RAISE 75% / CALL 25%:
- Two pair+
- OESD
- Top pair
- Overpair

CALL:
- everything else
- in particular: Gutshot, Second pair, Third pair, Underpair, all BDFD

Result: candidate **29.7 / 51.3 / 19.0** versus solver **30.4 / 51.6 / 18.0**. Local regret: **0.0362bb**.

The low class is the expensive part of the simplification. Extra BDFD mixing or splitting K-high boards can reduce local regret, but the gain is small relative to the additional rules.

## Package result

Approximate reach-weighted overall result of the preferred three-class package:

| | FOLD | CALL | RAISE |
|---|---:|---:|---:|
| **Solver** | **29.6%** | **55.2%** | **15.2%** |
| **Simplified** | **29.4%** | **54.9%** | **15.7%** |

Weighted local regret is approximately **0.0311bb**.

This is above the usual ~0.02bb simplification target because the broad K-low class deliberately preserves one simple hand rule across K-high, Q-to-8-high, and 7-to-4-high boards. The action-frequency shape is extremely well preserved: all three overall actions are within about half a percentage point of solver.

## Why not four classes?

A four-class version splitting `K[9-2]x` from `[Q-8]x + [7-4]x` was tested with constrained human-rule searches. Under a reasonable <=5pp per-class action-frequency constraint, the four-class package reaches about **0.0285bb** local regret.

The gain versus the three-class package is only about **0.0026bb**, but it requires a K-specific fold/raise rule and a separate flop class. This is not worth the added cognitive load, so the three-class taxonomy is preferred.

## Why not reuse the old BB defense?

Literal transfer of the existing BB-vs-UTG-B33 defense produces approximately **23.6 / 70.5 / 6.0** versus the NOD006 solver's **29.6 / 55.2 / 15.2**. Local regret is only about **0.0214bb**, but the range composition is badly distorted: too much call and far too little raise. The transfer is rejected.

## Why not remove raises?

A no-raise UTG response produces roughly **13.0 / 87.0 / 0.0** versus solver **29.6 / 55.2 / 15.2**. Local regret is about **0.0245bb**, but the action-frequency structure is destroyed. Unlike BTN defense versus UTG B33, UTG defense versus BTN stab needs a real raise component.

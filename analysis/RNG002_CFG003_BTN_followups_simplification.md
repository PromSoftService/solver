# RNG002 / CFG003 / NOD004 + NOD005 — BTN flop follow-up simplification

Datasets:

- `DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv`
- `DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv`

Spot: 6-max, 100bb, UTG open 2.5bb, BTN call, 6.5bb flop pot, 286 unpaired rainbow flops (`BRD001`). `NOD004` is BTN response after UTG bets 33%. `NOD005` is BTN stab after UTG checks. All aggregate frequencies and losses are weighted by `reach_probability`.

`local regret` is the weighted EV loss from the simplified action mixture against the opponent strategy in the solved equilibrium tree. It is useful for screening simplifications but is **not** exploitability after the opponent adapts.

## NOD005 — BTN stab after UTG CHECK

### Main conclusion

The preferred simplification **can reuse the same six flop classes and the same recognizable MIX hand pool already used for the UTG-vs-BB c-bet study**. A separate BTN-only flop taxonomy gives only a negligible EV improvement, so the shared taxonomy is the better human strategy.

Use the familiar six classes:

- `A[K-J]x`
- `A[T-2]x`
- `BBx`
- `K[9-2]x`
- `[Q-8]x`
- `[7-4]x`

Use the familiar MIX pool:

- Straight / Set / Two pair
- Overpair
- Top pair
- Second pair
- OESD
- Gutshot
- BDFD
- X-high

Always CHECK outside the MIX pool:

- Third pair
- Underpair
- Air / Nothing

Precedence: made hand first, then OESD, then Gutshot, then BDFD, then X-high, then Air.

### Simple 70 / 80 / 90 randomizer ladder

- `A[K-J]x` and `BBx` -> BET **70% MIX**.
- `A[T-2]x` and `K[9-2]x` -> BET **80% MIX**.
- `[Q-8]x` and `[7-4]x` -> BET **90% MIX**.

Result, sorted by solver BET frequency:

| Flop class | Solver BET | Simplified BET | Diff | Local regret |
|---|---:|---:|---:|---:|
| **[7-4]x** | 79.8% | 83.5% | +3.8 pp | 0.0019 bb |
| **[Q-8]x** | 67.2% | 65.1% | -2.1 pp | 0.0027 bb |
| **K[9-2]x** | 49.1% | 48.1% | -1.0 pp | 0.0030 bb |
| **A[T-2]x** | 46.4% | 42.6% | -3.9 pp | 0.0024 bb |
| **BBx** | 44.9% | 43.0% | -1.9 pp | 0.0068 bb |
| **A[K-J]x** | 39.3% | 38.7% | -0.5 pp | 0.0059 bb |
| **Overall** | **60.9%** | **59.4%** | **-1.5 pp** | **0.0032 bb** |

Every broad class is within 4 percentage points of the solver, overall frequency is within 1.5 points, and weighted local regret is about 0.0032bb.

A separately optimized four-class BTN taxonomy reaches about 0.0030bb local regret. The gain versus the shared six-class strategy is only about **0.0002bb**, which is not worth learning a second flop taxonomy. The shared six-class 70/80/90 ladder is therefore the preferred simplification.

## NOD004 — BTN defense versus UTG B33

### Solver aggregate

| Flop class | FOLD | CALL | RAISE |
|---|---:|---:|---:|
| **AKx** | **34.1%** | 59.0% | 6.9% |
| **Kxx** | **19.0%** | 74.4% | 6.6% |
| **[A/Q/J]xx** | **17.8%** | 74.9% | 7.3% |
| **[T-4]x** | **4.8%** | 85.7% | 9.5% |
| **Overall** | **19.0%** | **73.9%** | **7.1%** |

### Can the existing BB-vs-UTG-B33 defense be copied?

No. The literal existing BB-defense taxonomy/action matrix was evaluated on the BTN dataset and materially distorts the strategy:

| | Solver | Copied BB rule | Diff |
|---|---:|---:|---:|
| **FOLD** | 19.0% | 27.1% | +8.1 pp |
| **CALL** | 73.9% | 60.3% | -13.6 pp |
| **RAISE** | 7.1% | 12.6% | +5.5 pp |

Weighted local regret rises to **0.0264bb**. The distortion is not just an overall-frequency issue: for example, on `A[K-J]x` the copied rule folds 50.8% versus solver 31.4%, and on `K[9-2]x` it folds 36.9% versus solver 12.9%. BTN's preflop call range is too different from BB's range for a literal transfer to work.

Therefore forcing the old BB defense here is rejected.

### Recommended BTN defense

For this node the compact four broad classes work better:

- `AKx`
- `Kxx`
- `[A/Q/J]xx`
- `[T-4]x`

Definitions used below:

- `1OC` = exactly one hole card is an overcard to the flop.
- `2OC` = both hole cards are overcards to the flop.
- `BDFD 0OC` = backdoor flush draw with no overcard to the flop.
- `BDFD 1OC` = backdoor flush draw with exactly one overcard.
- `Underpair 9-` = pocket 99 or lower below the top flop card.
- Direct straight draws take precedence over BDFD / overcard labels.

#### FOLD layer

Apply first:

- Air / Nothing -> FOLD 100% on every class.
- X-high with exactly 1OC -> FOLD 100%.
- BDFD 0OC -> FOLD 100% on `AKx / Kxx / [A/Q/J]xx`; continue on `[T-4]x`.
- `[A/Q/J]xx + BDFD 1OC` -> FOLD 50% / continue 50%.
- `AKx + Underpair 9-` -> FOLD 75% / continue 25%.

Everything else continues.

#### RAISE layer

Among continuers:

- `AKx / Kxx`: Two pair+ -> RAISE 100%.
- `[A/Q/J]xx`: Two pair+ / OESD / Gutshot -> RAISE 40%, CALL 60%.
- `[T-4]x`: OESD / Gutshot -> RAISE 100%.
- Everything else -> CALL.

Result:

| Flop class | Solver F/C/R | Simplified F/C/R | Largest error | Local regret |
|---|---|---|---:|---:|
| **AKx** | 34.1 / 59.0 / 6.9 | 33.8 / 59.8 / 6.4 | 0.8 pp | 0.0073 bb |
| **Kxx** | 19.0 / 74.4 / 6.6 | 17.0 / 76.8 / 6.1 | 2.4 pp | 0.0090 bb |
| **[A/Q/J]xx** | 17.8 / 74.9 / 7.3 | 15.3 / 77.6 / 7.1 | 2.7 pp | 0.0160 bb |
| **[T-4]x** | 4.8 / 85.7 / 9.5 | 2.2 / 88.8 / 9.0 | 3.1 pp | 0.0411 bb |
| **Overall** | 19.0 / 73.9 / 7.1 | 16.9 / 76.4 / 6.8 | 2.5 pp | **0.0139 bb** |

The `[T-4]x` local-regret number is above the usual 0.02bb target because this broad low-board class contains heterogeneous combo-level mixing. Its reach weight at this node is small because UTG rarely reaches this node by betting low boards. Splitting low boards or individual hand ranks reduces that local number but materially increases complexity; the broad version is retained as the better human trade-off.

## What this says about reusable strategy modules

For **betting/stabbing**, reuse works extremely well: BTN after UTG checks can use the same six flop classes and essentially the same hand pool as the established UTG-vs-BB c-bet module, with different randomizer frequencies.

For **defense**, literal reuse is not automatically valid. BTN defense versus UTG B33 is a clear counterexample: copying the BB-vs-UTG-B33 matrix overfolds, undercalls, and overraises. The tailored BTN defense above is required.

The next still-unsolved branch is `UTG CHECK -> BTN BET33 -> UTG Fold / Call / Raise`. That is the correct place to test the user's desired second reuse: whether UTG's defense versus BTN stab can share the existing BB-defense flop/hand taxonomy. No conclusion about that node should be claimed from NOD004 because the acting range is different.

The strategies above are validated by equilibrium frequencies and local EV/regret only. They have not been strategy-locked and re-solved against an adapting opponent, so these local-regret values are not exploitability measurements.

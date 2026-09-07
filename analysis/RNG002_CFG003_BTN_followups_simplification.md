# RNG002 / CFG003 / NOD004 + NOD005 — BTN flop follow-up simplification

Datasets:

- `DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv`
- `DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv`

Spot: 6-max, 100bb, UTG open 2.5bb, BTN call, 6.5bb flop pot, 286 unpaired rainbow flops (`BRD001`). `NOD004` is BTN response after UTG bets 33%. `NOD005` is BTN stab after UTG checks. All aggregate frequencies and losses are weighted by `reach_probability`.

`local regret` below is the weighted EV loss from the simplified action mixture against the opponent strategy in the solved equilibrium tree. It is useful for screening simplifications but is **not** exploitability after the opponent adapts.

## NOD005 — BTN stab after UTG CHECK

### Solver aggregate

| Flop class | Solver BET |
|---|---:|
| **[T-4]x** | **74.9%** |
| **[A/Q/J]xx** | **51.8%** |
| **Kxx** | **45.8%** |
| **AKx** | **36.2%** |
| **Overall** | **60.9%** |

The direction is the reverse of UTG's OOP c-bet strategy: after UTG checks, BTN attacks low boards most aggressively and AKx least aggressively.

### Recommended simplification

Define the normal BTN stab pool as:

- Two pair+
- Overpair
- Top pair
- Second pair
- OESD
- Gutshot
- BDFD

Hands outside that pool are:

- Third pair
- Underpair
- X-high without a direct draw/BDFD
- Air / Nothing

Rules:

- **AKx:** use the pool **without BDFD**; BET 75% of that pool, CHECK everything else.
- **Kxx:** BET 100% of the normal pool, CHECK everything else.
- **[A/Q/J]xx:** BET 100% of the normal pool, CHECK everything else.
- **[T-4]x:** BET 75% of the **entire range**.

Result:

| Flop class | Solver BET | Simplified BET | Diff | Local regret |
|---|---:|---:|---:|---:|
| **[T-4]x** | 74.9% | 75.0% | +0.1 pp | 0.0037 bb |
| **[A/Q/J]xx** | 51.8% | 53.1% | +1.3 pp | 0.0020 bb |
| **Kxx** | 45.8% | 49.2% | +3.3 pp | 0.0037 bb |
| **AKx** | 36.2% | 34.2% | -1.9 pp | 0.0087 bb |
| **Overall** | 60.9% | 61.9% | +1.0 pp | **0.0030 bb** |

This is a strong same-complexity simplification: every broad flop class is within 3.4 percentage points of solver frequency and the weighted local regret is about 0.003bb.

## NOD004 — BTN defense versus UTG B33

### Solver aggregate

| Flop class | FOLD | CALL | RAISE |
|---|---:|---:|---:|
| **AKx** | **34.1%** | 59.0% | 6.9% |
| **Kxx** | **19.0%** | 74.4% | 6.6% |
| **[A/Q/J]xx** | **17.8%** | 74.9% | 7.3% |
| **[T-4]x** | **4.8%** | 85.7% | 9.5% |
| **Overall** | **19.0%** | **73.9%** | **7.1%** |

The main structural point is very clear: BTN folds much more on AKx and almost never folds low boards. A single board-independent defense rule loses too much information.

### Extra definitions needed for the simplified defense

- `1OC` = exactly one hole card is an overcard to the flop.
- `2OC` = both hole cards are overcards to the flop.
- `BDFD 0OC` = backdoor flush draw with no overcard to the flop.
- `BDFD 1OC` = backdoor flush draw with exactly one overcard.
- `Underpair 9-` = pocket 99 or lower below the top flop card.

Direct straight draws take precedence over BDFD/overcard labels.

### FOLD layer

Apply these first:

- **Air / Nothing:** FOLD 100% on every flop class.
- **X-high with exactly 1OC:** FOLD 100%.
- **BDFD 0OC:** FOLD 100% on **AKx / Kxx / [A/Q/J]xx**; continue on `[T-4]x`.
- **[A/Q/J]xx + BDFD 1OC:** FOLD 50% / continue 50%.
- **AKx + Underpair 9-:** FOLD 75% / continue 25%.

Everything not folded goes to the continue layer.

### RAISE layer

Among hands that continue:

- **AKx / Kxx:** Two pair+ → RAISE 100%.
- **[A/Q/J]xx:** Two pair+ / OESD / Gutshot → RAISE 40%, CALL 60%.
- **[T-4]x:** OESD / Gutshot → RAISE 100%.
- Everything else → CALL.

Result:

| Flop class | Solver F/C/R | Simplified F/C/R | Largest frequency error | Local regret |
|---|---|---|---:|---:|
| **AKx** | 34.1 / 59.0 / 6.9 | 33.8 / 59.8 / 6.4 | 0.8 pp | 0.0073 bb |
| **Kxx** | 19.0 / 74.4 / 6.6 | 17.0 / 76.8 / 6.1 | 2.4 pp | 0.0090 bb |
| **[A/Q/J]xx** | 17.8 / 74.9 / 7.3 | 15.3 / 77.6 / 7.1 | 2.7 pp | 0.0160 bb |
| **[T-4]x** | 4.8 / 85.7 / 9.5 | 2.2 / 88.8 / 9.0 | 3.1 pp | 0.0411 bb |
| **Overall** | 19.0 / 73.9 / 7.1 | 16.9 / 76.4 / 6.8 | 2.5 pp | **0.0139 bb** |

The `[T-4]x` local-regret number is noticeably higher than the other classes because this very broad class contains substantial combo-level mixing that is not captured by a small set of hand labels. Its reach weight at this node is small because UTG rarely arrives here through B33 on low boards. Splitting low boards or individual hand ranks can reduce this number, but that would materially increase strategy complexity. For the requested human simplification the broad rule above is the better trade-off.

## Practical conclusions

For BTN stab after UTG checks, the four existing flop classes work extremely well and the final strategy is very compact. For BTN defense versus UTG B33, the same four classes are still usable, but defense needs two extra hand-quality distinctions: number of overcards and whether a BDFD has an overcard. Those distinctions recover the solver's fold structure without forcing strong made hands or direct draws into bad folds.

The strategy is validated by equilibrium frequencies and local EV/regret only. It has not been strategy-locked and re-solved against an adapting opponent, so the numbers above must not be described as exploitability or proof of near-GTO play.

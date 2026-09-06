# UTG c-bet 1/3 — frequency-aware reanalysis

Dataset: `DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv`.

The legacy 13 texture buckets were re-evaluated against the current TexasSolverGPU B33-only tree. The old headline frequencies came from a different multi-size source and should not be treated as current equilibrium frequencies.

## Legacy texture buckets: old headline vs current B33 solve

| Legacy class | Old headline | Current B33 c-bet |
|---|---:|---:|
| ABB | 90% | 98.4% |
| A[K/Q]x | 85% | 89.7% |
| BBB | 80–85% | 88.6% |
| BBx dis | 80–85% | 88.4% |
| K/Qx dis | 80% | 73.2% |
| A[J–T][9–5] | 60–70% | 79.6% |
| K/Qx con | 60–65% | 61.5% |
| A[9–7]x | 55% | 55.7% |
| [J–8]x dis | 55% | 55.4% |
| A[J–T][4–2] | 50% | 67.6% |
| [J–8]x con | 50% | 46.7% |
| [7–4]x | 50% | 13.3% |
| A[6–2] | 35% | 29.6% |

The current legacy trainer lists contain 127 representative unpaired-rainbow rank triples, not a complete partition of all 286 canonical unpaired-rainbow flops. Therefore this report validates/compresses the legacy texture scaffold, but a final strategy still needs complete 286-flop classification rules.

## Texture compression

The 13 legacy labels can be compressed reasonably to six texture/frequency groups:

- `HIGH`: ABB + A[K/Q]x + BBB + BBx dis
- `BET75`: K/Qx dis + A[J–T][9–5] + A[J–T][4–2]
- `MID55`: K/Qx con + A[9–7]x + [J–8]x dis
- `CON47`: [J–8]x con
- `A_LOW30`: A[6–2]
- `LOW13`: [7–4]x

| Group | Solver c-bet | Board-frequency MAE inside group |
|---|---:|---:|
| HIGH | 90.6% | 6.4 pp |
| BET75 | 74.3% | 6.1 pp |
| MID55 | 57.4% | 8.8 pp |
| CON47 | 46.7% | 14.5 pp |
| A_LOW30 | 29.6% | 10.6 pp |
| LOW13 | 13.3% | 8.4 pp |

`CON47` is notably heterogeneous even before hand class is considered: its boards range from 9.4% to 74.5% c-bet. It should not be merged further without a better connected-board subdivision.

## Current solver c-bet frequency by hand class and compressed texture

| Hand class | HIGH | BET75 | MID55 | CON47 | A_LOW30 | LOW13 |
|---|---:|---:|---:|---:|---:|---:|
| Two pair+ | 98.0 | 97.0 | 94.5 | 78.9 | 70.7 | 45.6 |
| Overpair | 98.5 | 92.9 | 67.1 | 49.2 | — | 15.0 |
| Underpair | 86.5 | 62.6 | 46.7 | 38.6 | 20.4 | 14.6 |
| Top pair | 91.4 | 73.8 | 57.8 | 55.7 | 27.2 | 31.1 |
| Second pair | 90.2 | 76.0 | 83.8 | 42.9 | 74.2 | 21.2 |
| Third pair | 87.7 | 83.9 | 72.6 | 23.9 | 62.7 | 19.9 |
| Weak pocket pair | 81.8 | 61.1 | 38.4 | 15.5 | 28.0 | 0.0 |
| OESD | 96.0 | 91.9 | 93.0 | 62.8 | 75.8 | 13.1 |
| Gutshot | 93.5 | 84.6 | 80.0 | 53.9 | 52.0 | 12.8 |
| BDFD | 88.3 | 68.6 | 49.6 | 29.8 | 23.5 | 9.7 |
| 2 overcards | — | 54.5 | 46.0 | 36.1 | — | 10.9 |
| Air | 95.3 | 72.6 | 62.4 | 51.8 | 35.5 | 12.8 |

Two useful corrections to the old human table follow from this:

1. `OESD` should be split from `Gutshot`. The old trainer routed both into the row labelled “Gutshot”, but their current frequencies differ materially on several texture groups.
2. `2 overcards` should be split from generic `Air`. For example on `BET75`, 2 overcards bet 54.5% while residual Air bets 72.6%; on `MID55`, 46.0% vs 62.4%.

## Frequency simplification tests

Four ways of rounding each hand-class/texture cell were compared. The table below reports resulting total c-bet frequency and local action regret against the equilibrium BB strategy.

| Scheme | Frequency levels | Solver total | Simplified total | Delta | Local regret |
|---|---|---:|---:|---:|---:|
| PURE_NEAREST | 0 / 100 | 61.7% | 65.4% | +3.7 pp | 0.0026 bb |
| MIX50_NEAREST | 0 / 50 / 100 | 61.7% | 60.8% | -0.9 pp | 0.0031 bb |
| QUARTERS | 0 / 25 / 50 / 75 / 100 | 61.7% | 61.9% | +0.1 pp | 0.0034 bb |
| MIX50_30_70 | 0 / 50 / 100 with 30/70 thresholds | 61.7% | 63.2% | +1.5 pp | 0.0028 bb |

The total frequency alone hides texture distortion. For `MIX50_NEAREST`, for example, `HIGH` becomes 100% instead of 90.6%, `BET75` falls to 65.2% instead of 74.3%, and `LOW13` falls to 2.2% instead of 13.3%. The errors happen to cancel in the total.

Quarter-frequency rounding preserves texture frequencies much better:

| Group | Solver | QUARTERS | Delta |
|---|---:|---:|---:|
| HIGH | 90.6% | 95.2% | +4.6 pp |
| BET75 | 74.3% | 74.8% | +0.5 pp |
| MID55 | 57.4% | 55.1% | -2.3 pp |
| CON47 | 46.7% | 44.5% | -2.1 pp |
| A_LOW30 | 29.6% | 27.9% | -1.7 pp |
| LOW13 | 13.3% | 11.6% | -1.7 pp |

## Candidate equilibrium-aware human matrix

Numbers are c-bet frequencies. They are rounded to quarters, not exact solver frequencies.

| Hand class | HIGH | BET75 | MID55 | CON47 | A_LOW30 | LOW13 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Two pair+** | 100 | 100 | 100 | 75 | 75 | 50 |
| **Overpair** | 100 | 100 | 75 | 50 | — | 25 |
| **Underpair** | 75 | 75 | 50 | 50 | 25 | 25 |
| **Top pair** | 100 | 75 | 50 | 50 | 25 | 25 |
| **Second pair** | 100 | 75 | 75 | 50 | 75 | 25 |
| **Third pair** | 100 | 75 | 75 | 25 | 75 | 25 |
| **Weak pocket pair** | 75 | 50 | 50 | 25 | 25 | 0 |
| **OESD** | 100 | 100 | 100 | 75 | 75 | 25 |
| **Gutshot** | 100 | 75 | 75 | 50 | 50 | 25 |
| **BDFD** | 100 | 75 | 50 | 25 | 25 | 0 |
| **2 overcards** | — | 50 | 50 | 25 | — | 0 |
| **Air** | 100 | 75 | 50 | 50 | 25 | 25 |

This is a candidate simplification, not a proof of exploitability. `loss_if_bet/check` is local regret versus the equilibrium BB strategy. A best-response/re-solve against the simplified strategy is still required before claiming that the quarter-rounded strategy itself is near-equilibrium.

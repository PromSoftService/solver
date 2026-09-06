# UTG flop c-bet 1/3 — refined human strategy

Source: `datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv` (RNG001, BRD001, 286 canonical unpaired rainbow flops). Spot: UTG open 2.5bb, BB call; flop BB check; UTG chooses Check or Bet 1/3.

The goal is not to reproduce every solver mix. It is to choose deterministic hand buckets while keeping the important range composition and approximate board-class c-bet frequencies.

## Solver c-bet frequencies by the six established flop classes

| Flop class | Solver Bet |
|---|---:|
| A[K-J]x | 88.2% |
| A[T-2]x | 52.9% |
| BBx | 87.0% |
| K[9-2]x | 70.5% |
| [Q-8]x | 57.8% |
| [7-4]x | 16.5% |

## Recommended deterministic matrix

Action precedence: made hand first; then direct draw (OESD/Gutshot); then BDFD; then two overcards; then Air. `BDFD` means no made hand and no direct straight draw. `2 overcards` means no made hand/direct draw/BDFD already classified. BDSD-only follows Air unless the hand is already in `2 overcards`.

| Hand category | A[K-J]x | A[T-2]x | BBx | K[9-2]x | [Q-8]x | [7-4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Two pair+** | **BET** | **BET** | **BET** | **BET** | **BET** | **CHECK** |
| **Top pair** | **BET** | **CHECK** | **BET** | **CHECK** | **BET** | **CHECK** |
| **Any other pair**¹ | **BET** | **BET** | **BET** | **BET** | **BET** | **CHECK** |
| **OESD / Gutshot** | **BET** | **BET** | **BET** | **BET** | **BET** | **CHECK** |
| **BDFD** | **BET** | **BET** | **BET** | **BET** | **CHECK** | **CHECK** |
| **2 overcards** | — | — | —² | — | **CHECK** | **CHECK** |
| **Air** | **BET** | **CHECK** | **BET** | **BET** | **BET** | **CHECK** |

¹ Overpair, underpair / pocket pair, second pair, third pair.  
² On BBx, the relevant two-overcard hands effectively carry a direct straight draw and are handled by `OESD / Gutshot`.

This can be compressed mentally to:

- `A[K-J]x` and `BBx`: range BET.
- `[7-4]x`: range CHECK.
- `A[T-2]x`: CHECK top pair and Air; BET everything else.
- `K[9-2]x`: CHECK top pair; BET everything else.
- `[Q-8]x`: BET made hands and direct draws; CHECK BDFD-only and two-overcard no-direct-draw hands; BET remaining Air.

## Resulting frequencies and EV cost

| Flop class | Solver Bet | Simplified Bet | Reach-weighted selected-action loss |
|---|---:|---:|---:|
| A[K-J]x | 87.9% reach-weighted / 88.2% board-average | 100.0% | 0.0002bb |
| A[T-2]x | 52.5% / 52.9% | 50.4% | 0.0034bb |
| BBx | 86.9% / 87.0% | 100.0% | 0.0003bb |
| K[9-2]x | 70.3% / 70.5% | 76.6% | 0.0055bb |
| [Q-8]x | 57.5% / 57.8% | 57.1% | 0.0069bb |
| [7-4]x | 16.5% / 16.5% | 0.0% | 0.0019bb |

Across the full dataset, the reach-weighted loss of the selected deterministic actions is about **0.0042bb per UTG flop decision** relative to choosing the best pure action combo-by-combo from the solved node.

## Why no 50/50 randomizer

A solver mixing one combo does not mean a human must randomize that combo. However, purifying every mixed combo in the same direction can destroy the composition of the overall betting/checking ranges. The matrix above deliberately uses natural deterministic buckets to keep the middle board classes close to the solver's aggregate frequencies while maintaining value in the checking range (especially Top pair on A[T-2]x and K[9-2]x). On the extreme classes, `A[K-J]x`/`BBx` are simplified to range bet and `[7-4]x` to range check because the measured pure-action cost is tiny.

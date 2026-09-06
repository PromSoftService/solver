# BRD001 solver-like strategy summary

Source dataset: `DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv` (106381 combo rows, 286 canonical unpaired rainbow flops).

Method: for each flop, BB combos are weighted by solver reach; flop-level action frequencies are then averaged equally inside each board class. Pure-action EV-loss values below are reach-weighted averages in bb. Practical simplification threshold: 0.02bb.

## Board-class frequencies

| Flop class | SDF | Call | Raise |
|---|---:|---:|---:|
| A[K-J]x | 48.0% | 36.3% | 11.7% |
| A[T-2]x | 57.1% | 43.1% | 14.0% |
| BBx | 56.3% | 42.4% | 13.8% |
| K[9-2]x | 62.9% | 47.8% | 15.0% |
| [Q-8]x | 70.3% | 53.7% | 16.6% |
| [7-4]x con | 72.3% | 54.2% | 18.1% |
| [7-4]x dis | 72.5% | 54.1% | 18.5% |
| [7-4]x merged | 72.4% | 54.1% | 18.3% |

The con/dis split is not useful in BRD001: the two low-board classes are almost identical at the aggregate level.

## Category evidence

| Category | Solver aggregate | Best simple action | Mean EV loss of simple action |
|---|---|---|---:|
| Top pair | C 89.2 / R 10.8 | C | 0.0027 |
| Second pair | C 84.4 / R 14.8 | C | 0.0058 |
| Third pair | C 75.7 / R 20.8 | C | 0.0115 |
| High underpair | C 97.3 | C | 0.0008 |
| Overpair | C 87.8 / R 12.2 | C | 0.0015 |
| OESD / 8-out | C 32.8 / R 66.1 | R | 0.0082 |
| Gutshot | C 53.6 / R 38.0 | split by BDFD | — |
| Overcards + BDFD | C 54.1 / R 25.2 / F 20.7 | C | 0.0107 |
| BDFD only | F 96.6 | F | 0.0035 |
| BDFD + BDSD | F 83.9 / C 7.7 / R 8.4 | F | 0.0280 |
| Air / Nothing | F 84.4 / C 15.6 | F | 0.0073 |
| Bare AK | C 100 | C | 0.0000 |
| Bare AQ | C 99.6 | C | 0.0000 |

### Gutshots

The clean practical split is:

- naked gutshot: mostly call;
- gutshot + BDFD: much more raise-heavy, so use raise as the simple action.

Examples: on A[T-2]x naked gutshots are C 73.6 / R 25.3, while gutshot+BDFD is C 36.5 / R 63.2. On K[9-2]x naked gutshots are C 65.2 / R 34.8, while gutshot+BDFD is C 23.2 / R 76.8.

### Weak pocket pairs

Weak pair = pocket pair below the middle flop rank.

- A[K-J]x: F 96.0%, mean fold loss 0.0064 -> fold.
- A[T-2]x is heterogeneous. The useful boundary is the second flop rank:
  - AKx/AQx/AJx/ATx: fold (roughly 92-97% solver fold; fold loss about 0.002-0.011).
  - A9x and lower: call is the better simple action (call loss near zero).
- BBx: fold is the simplest acceptable rule; solver is roughly F 69 / C 31 and F/C EV are often close.
- K[9-2]x and lower: call.

### Strong made hands

On A-high through [Q-8] boards, `Two pair+ -> Raise` is a good simplification. On very low [7-4] boards the composition changes: sets/two pair are often better simplified to call, while made straights remain raises. This is the main low-board exception worth remembering.

### Bare high cards

- Bare AK: call on Q-high and lower.
- Bare AQ: call on K-low/Q-low and lower when unpaired/no direct draw.
- Bare AJ: fold on K[9-2]x, but call on [Q-8]x and low boards is a useful exception.
- KQ and weaker no-draw high cards can remain folds for a simple strategy; KQ is borderline in some lower classes but the EV cost of folding is generally small enough for the 0.02bb-style simplification.

## Human strategy matrix

| Hand category | A[K-J]x | A[T-2]x | BBx | K[9-2]x | [Q-8]x | [7-4]x con | [7-4]x dis |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Strong value: set / two pair | R | R | R | R | R | C | C |
| Made straight | R | R | R | R | R | R | R |
| Normal pair: overpair / high underpair / top / 2nd / 3rd | C | C | C | C | C | C | C |
| Weak pocket pair | F | F/C* | F | C | C | C | C |
| OESD | R | R | R | R | R | R | R |
| Gutshot + BDFD | R | R | R | R | R | R | R |
| Naked gutshot | C | C | C | C | C | C | C |
| Two overcards + BDFD | — | — | — | — | C | C | C |
| Bare AK / AQ | — | — | — | C | C | C | C |
| Bare AJ | — | — | — | F | C | C | C |
| BDFD + BDSD only | F | F | F | F | F | F | F |
| BDFD only / BDSD only / Air | F | F | F | F | F | F | F |

`F/C*` on A[T-2]x weak pairs: fold on ATx and higher; call on A9x and lower.

This matrix is intentionally solver-like rather than an attempt to reproduce every mixed strategy. It prioritizes low complexity and low pure-action EV loss.

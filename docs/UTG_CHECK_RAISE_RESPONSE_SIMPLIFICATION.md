# UTG response to BB check-raise: approved manual simplification

## Scope

This is the user-approved human table for `STU002 / 04_UTG_AFTER_CHECK_RAISE`:
`BB CHECK -> UTG BET 1/2 -> BB CHECK-RAISE 60 -> UTG FOLD/CALL`.
It is a manual interpretation of the tracked solver export, not generated output.
The production workbook generator neither reads nor writes this table.

The audit used 75,236 positive-reach combo rows. The exhaustive partition is:
`ABB / BBB` (10 boards), `Axx / Bxx` excluding the first class (220 boards),
and `[9-2]xx` (56 boards).

## Approved table

| Hand category | ABB / BBB | Axx / Bxx | [9-2]xx |
|---|---:|---:|---:|
| Two pair+ | C | C | C |
| Overpair | — | C | C |
| Top pair | BDFD | C | C |
| Underpair | — | C | C |
| Second pair | F | C | C |
| Weak pair | — | F | C |
| Third pair | F | C | C |
| Low pocket pair | F | F | F |
| OESD | C | C | C |
| Gutshot | PAIR | C | C |
| 2 overcards + BDFD | — | C | C |
| Air | F | F | BDFD |

`BDFD` means CALL with a backdoor flush draw, otherwise FOLD. `PAIR` means
CALL when the Gutshot also has a made pair, otherwise FOLD. Draws retain
priority over made-hand rows.

## Audit and accepted trade-off

| Metric | Solver | Approved table | Delta |
|---|---:|---:|---:|
| FOLD | 39.2341% | 37.1501% | -2.0840 pp |
| CALL | 60.7659% | 62.8499% | +2.0840 pp |

- mean source loss: 0.156224 bb locally, 0.010637 bb at root;
- mean clipped source loss: 0.168665 bb locally, 0.011484 bb at root;
- mean oracle regret: 0.177247 bb locally, 0.012068 bb at root;
- local P95/P99 oracle regret: 0.560665/5.015470 bb;
- reach above 0.5/1.0 bb local regret: 5.2160%/3.8886%.

The simplification deliberately calls Second pair and Gutshot more often while
folding Weak pair and Air more often. This preserves a human-readable strength
ordering. The remaining large local tail is concentrated in rare naked
Gutshots; removing it would require more flop classes or hidden selectors.

Keeping five classes and a separate `Second pair / Axx = SUITED` rule saves
only about 0.000345 bb at root. Merging ABB with BBB costs about 0.000041 bb at
root and 0.019 percentage points of CALL. The user explicitly accepted the
three-column compromise after independent GPT-6 Astra review and local
reproduction from the tracked data.

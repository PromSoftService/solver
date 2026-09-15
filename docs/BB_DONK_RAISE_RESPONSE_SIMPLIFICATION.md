# BB response to UTG donk-raise: approved manual simplification

## Scope and provenance

This is the user-approved human table for
`STU002 / 06_BB_AFTER_DONK_RAISE`: after `BB DONK 1/2 -> UTG RAISE 60`,
BB chooses FOLD or CALL.

The numerical source is the tracked aggregate export
`datasets/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/06_BB_AFTER_DONK_RAISE/20260909-024314Z/combos.csv`.
The audit used 57,240 positive-reach combo rows and all 286 BRD001 boards.
The node reach from the flop root is 0.0082446. No GPU solve was launched.

This is a manually reviewed teaching artifact. The production generator still
creates only the canonical solver-frequency workbook and does not consume this
table.

## Approved table

| Hand category | ABB / BBB | Axx / Bxx | [9-2]xx |
|---|---:|---:|---:|
| Two pair+ | C | C | C |
| Overpair | - | C | C |
| Top pair | C | C | C |
| Underpair | - | F | C |
| Second pair | F | C | C |
| Weak pair | - | F | F |
| Third pair | F | F | C |
| Low pocket pair | F | F | F |
| OESD | C | C | C |
| Gutshot | PAIR/BDFD | PAIR/BDFD | PAIR/BDFD |
| 2 overcards + BDFD | - | Ax | Ax |
| Air | F | F | F |

`PAIR/BDFD` means CALL when the Gutshot also has any made pair or BDFD,
otherwise FOLD. `Ax` means CALL when either hole card is an ace, otherwise
FOLD. Draw rows retain priority over made hands.

The exhaustive partition is `ABB / BBB` (10 boards), non-ABB/BBB
`Axx / Bxx` (220), and `[9-2]xx` (56).

## Rare deep-branch rule

After a second aggressive flop action in a low-reach branch, prefer a pure
value-and-strong-draw response over preserving every solver mix. Keep strong
made hands and OESD; split marginal pairs only at one familiar high/low board
boundary; use a row-wide observable selector only when it separates materially
different solver decisions and EV.

A larger local discrepancy is acceptable only when node-wide frequencies,
root-scaled loss, subgroup direction and the loss tail are reported. This rule
is branch-specific and does not relax the standard for common nodes.

For this branch, the Gutshot selector is supported: solver CALL is 82.28% on
the selected pair-or-BDFD reach and 33.34% on the rejected reach. The Ax
selector is stronger: solver CALL is 73.95% with an ace and 4.35% without one
inside the two-overcards-plus-BDFD row.

## Reproduced audit

| Metric | Solver | Old five-column table | Approved table |
|---|---:|---:|---:|
| FOLD | 41.4759% | 37.5123% | 40.5923% |
| CALL | 58.5241% | 62.4877% | 59.4077% |
| Root source loss | - | 0.000292 bb | 0.000282 bb |
| Root clipped loss | - | 0.000305 bb | 0.000298 bb |
| Local oracle P99 | - | 1.0972 bb | 1.1447 bb |
| Reach above 1.0 bb | - | 1.2123% | 1.3527% |

The approved CALL deviation is +0.8836 percentage points. Mean local
source/clipped/oracle loss is 0.034226/0.036124/0.037948 bb. The new table
slightly improves mean and root loss while accepting a small worsening of P99
and the reach above 1 bb.

The main hidden distortion is paired Broadway: it is only 0.162% of node reach,
but the candidate calls 99.81% versus solver 67.11%. The known largest errors
are unpaired BDFD Gutshots on T97-type boards, already present in the old
PAIR/BDFD cells. GPT-6 Astra independently reviewed the reproduced evidence,
accepted the candidate for this rare branch, and identified no supported
row-wide replacement that was clearly better.

These are fixed-opponent local EV/regret checks, not exploitability or proof
against an adapting opponent.

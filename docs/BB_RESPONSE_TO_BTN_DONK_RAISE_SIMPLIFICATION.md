# BB response to BTN donk-raise: approved human simplification

## 1. Scope and source

This document records the user-approved teaching strategy for
`STU005 / 06_BB_AFTER_DONK_RAISE`: after
`BB DONK BET 1/2 -> BTN RAISE 60`, BB chooses FOLD or CALL.

The numerical source is the completed combo-level export
`20260915-055252Z/06_BB_AFTER_DONK_RAISE/combos.csv`: 150,051 rows, of which
73,666 have positive reach. All 286 boards passed validation. The solver,
production generator, canonical workbook and source dataset are unchanged.
This table is a manual teaching layer and is not generated or consumed by
repository code.

The shared hand priority is mandatory:

`OESD -> Gutshot -> made hand -> 2 overcards + BDFD -> Air`.

## 2. Approved table

Defense/response display order is
`ABB -> BBB -> Axx -> K/Qxx -> J/Txx -> [9-2]xx`.

| Hand category | ABB | BBB | Axx | K/Qxx | J/Txx | [9-2]xx |
|---|---:|---:|---:|---:|---:|---:|
| Two pair+ | C | C | C | C | C | C |
| Overpair | — | — | — | — | — | C |
| Top pair | C | C | C | C | C | C |
| Underpair | — | — | C | C | C | C |
| Second pair | BDFD | BDFD | C | C | C | C |
| Weak pair | — | — | F | F | F | F |
| Third pair | F | F | BDFD | C | C | C |
| Low pocket pair | F | F | F | F | F | F |
| OESD | C | C | C | C | C | C |
| Gutshot | PAIR | PAIR | PAIR/BDFD | C | C | C |
| 2 overcards + BDFD | — | — | — | — | Ax | Ax |
| Air | — | — | F | F | F | F |

`BDFD` means CALL with a backdoor flush draw and FOLD without one. `PAIR`
means CALL when the Gutshot also contains any made pair and FOLD otherwise.
`PAIR/BDFD` calls with either property. `Ax` calls when one hole card is an
ace and folds otherwise. These are deterministic observable selectors, not
randomizers. `—` means the category is absent at that class.

The six classes contain 6 / 4 / 60 / 96 / 64 / 56 boards and cover all
286 BRD001 flops exactly once.

## 3. Strategic structure

Two pair+, Top pair and OESD always call after BTN raises. Weak pair, Low
pocket pair and Air always fold. The middle pairs form simple strength
transitions as the board becomes less Broadway-dense.

Second pair needs BDFD on `ABB/BBB` and calls from Axx downward. Third pair
folds on `ABB/BBB`, needs BDFD on Axx and calls from K/Qxx downward. This
keeps the learnable progression `FOLD -> BDFD -> CALL` rather than restoring
a low-board BDFD exception for a negligible root-EV gain.

Gutshot uses the same strength progression: a made pair on dense Broadway,
a made pair or BDFD on Axx, then pure CALL from K/Qxx downward. The
two-overcards row uses one `Ax` rule wherever it exists. Air remains pure
FOLD instead of inheriting rare solver calls.

## 4. Reproduced audit

| Metric | Solver | Candidate | Delta |
|---|---:|---:|---:|
| FOLD | 41.9091% | 33.6057% | -8.3034 pp |
| CALL | 58.0909% | 66.3943% | +8.3034 pp |

- branch reach relative to the solver flop root: 0.4122%;
- mean reach-weighted local source loss: 0.048328 bb;
- root-normalized source loss: 0.000199 bb;
- mean local oracle regret: 0.049781 bb;
- root-normalized oracle regret: 0.000205 bb;
- oracle-regret P95 / P99 / P99.9: 0.397070 / 0.993524 / 1.782604 bb;
- reach above 0.50 / 1.00 bb oracle regret: 3.8322% / 0.9749%;
- maximum single-combo oracle regret: 2.297268 bb.

The table deliberately over-calls by 8.30 percentage points. This is accepted
only for this very deep branch: it reaches 0.4122% from the solved flop root,
so the root-normalized source loss is about two ten-thousandths of a blind.
The local loss and tail remain explicit because root scaling must not hide
weak individual decisions.

A more exact Third-pair rule restored BDFD on `[9-2]xx`. It reduced local
source loss from 0.048328 to 0.047648 bb, but broke the monotone
`FOLD -> BDFD -> CALL` progression. The root gain was below 0.000003 bb, so
the user approved the simpler transition.

## 5. Reachability and trainer exception

Baseline `5.4.1` makes BB range CHECK, so neither this branch nor its parent
is reachable against the approved baseline. The user separately approved
`5.4.5 BB DONK 1/2 -> BTN RESPONSE` as an all-six-class opponent-deviation
exercise against humans who may donk incorrectly.

Inside that deviation mode, `5.4.5` can RAISE with Two pair+, OESD and
Gutshot on every flop class. Therefore the standalone trainer must also make
`5.4.6` reachable on all six classes whenever the generated preceding BTN
action is RAISE. This downstream exception does not change `5.4.1`, invent a
solver donk frequency or authorize unrelated off-policy histories.

The 0.4122% reach above describes the solved source tree and is reported for
audit normalization. It is not the sampling frequency for the deviation
exercise.

## 6. Approval and scope boundary

The user approved this exact six-column candidate on 2026-09-17. Approval is
branch-specific: identical class names do not permit its actions to be copied
to another position or history.

The standalone trainer file is intentionally not changed in this
approval-only commit. The mandatory deviation path through both `5.4.5` and
`5.4.6` must be implemented with the complete approved BTN-vs-BB strategy in
the next publication pass.

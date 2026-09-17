# BTN response to BB check-raise: approved human simplification

## 1. Scope and source

This document records the user-approved teaching strategy for
`STU005 / 04_BTN_AFTER_CHECK_RAISE`: after
`BB CHECK -> BTN BET 1/2 -> BB RAISE 60`, BTN chooses FOLD or CALL.

The numerical source is the completed combo-level export
`20260915-055252Z/04_BTN_AFTER_CHECK_RAISE/combos.csv`: 153,604 rows,
of which 141,866 have positive reach. All 286 boards passed validation.
The solver, production generator, canonical workbook and source dataset are
unchanged. This table is a manual teaching layer and is not generated or
consumed by repository code.

The shared hand priority is mandatory:

`OESD -> Gutshot -> made hand -> 2 overcards + BDFD -> Air`.

## 2. Approved table

Defense/response display order is
`ABB -> BBB -> Axx -> K/Qxx -> J/Txx -> [9-2]xx`.

| Hand category | ABB | BBB | Axx | K/Qxx | J/Txx | [9-2]xx |
|---|---:|---:|---:|---:|---:|---:|
| Two pair+ | C | C | C | C | C | C |
| Overpair | — | — | — | C | C | C |
| Top pair | BDFD | BDFD | C | C | C | C |
| Underpair | — | — | C | C | C | C |
| Second pair | BDFD | BDFD | C | C | C | C |
| Weak pair | — | — | C | C | C | C |
| Third pair | BDFD | BDFD | C | C | C | C |
| Low pocket pair | F | F | F | F | F | F |
| OESD | C | C | C | C | C | C |
| Gutshot | PAIR | PAIR | C | C | C | C |
| 2 overcards + BDFD | — | — | — | C | C | C |
| Air | F | F | F | F | F | F |

`BDFD` means CALL with a backdoor flush draw and FOLD without one.
`PAIR` means CALL when the Gutshot also contains any made pair and FOLD
without a made pair. Both are deterministic observable selectors, not
randomizers. `—` means the category is absent at that class.

The six classes are mutually exclusive and exhaustive. Their board counts are
6 / 4 / 60 / 96 / 64 / 56, totaling all 286 BRD001 flops.

## 3. Selector evidence

Dense-Broadway Top pair strongly separates by BDFD: on BBB the BDFD subgroup
calls about 91.4% while the no-BDFD subgroup calls only about 1.6%. On ABB the
same split is 100% versus about 42.9%, so the shared selector deliberately
folds part of a mixed no-BDFD subgroup to avoid a separate exception.

Second pair with BDFD calls essentially 100% on ABB and about 73.7% on BBB;
without BDFD both subgroups fold. Third pair with BDFD calls about 87.2% on
ABB and 48.5% on BBB, while both no-BDFD subgroups fold. Keeping one BDFD
rule across dense Broadway boards avoids a tiny BBB-only exception.
Paired Gutshots call essentially 100% on ABB and about 81.0% on BBB. Unpaired
Gutshots call only about 46.1% and 24.4%, respectively, so `PAIR` gives a
clean observable boundary.

## 4. Strategic structure

Two pair+, overpairs, ordinary pairs and direct draws form the CALL range.
On `ABB/BBB`, vulnerable pairs require BDFD and Gutshot requires a made
pair. From `Axx` downward normal pairs and all direct draws call.

Low pocket pair and Air always fold. This deliberately removes rare solver
calls with weak holdings and avoids over-calling after BB has already
check-raised.

Gutshot remains pure CALL from Axx downward even though a few concrete
J/T-high combinations prefer FOLD strongly. Solver calls the J/T-high
Gutshot row about 89.7% overall. Replacing it with `PAIR/BDFD` doubled mean
local loss from about 0.0237 to 0.0500 bb and created much worse tails, so the
extra micro-rule was rejected.

## 5. Reproduced audit

| Metric | Solver | Candidate | Delta |
|---|---:|---:|---:|
| FOLD | 40.0662% | 42.2941% | +2.2280 pp |
| CALL | 59.9338% | 57.7059% | -2.2280 pp |

- branch reach relative to the flop root: 6.0416%;
- mean reach-weighted local source loss: 0.023685 bb;
- root-normalized source loss: 0.001431 bb;
- mean local oracle regret: 0.024299 bb;
- root-normalized oracle regret: 0.001468 bb;
- oracle-regret P95 / P99 / P99.9: 0.094540 / 0.698544 / 1.521132 bb;
- reach above 0.50 / 1.00 bb oracle regret: 1.8670% / 0.2988%;
- maximum single-combo oracle regret: 2.003700 bb.
The main residual tail is `Gutshot / J/Txx`: some weak unpaired Gutshots are
forced to CALL. The alternative observable filters were tested and rejected
because they folded too many of the row's roughly 90% solver calls and
materially increased both mean loss and the tail.

The local mean slightly exceeds the 0.020 bb warning used for the shallower
STU002 defense example. This is accepted branch-specifically because total
continuation differs by only 2.23 percentage points and the node is reached
only 6.04% from the flop root, leaving root-normalized loss at 0.001431 bb.

## 6. Approval and scope boundary

All six classes are reachable through the approved upstream BTN c-bet and BB
check-raise model; none of these columns is documentation-only on the normal
training path.

The user approved this exact six-column candidate on 2026-09-17. Approval is
branch-specific: identical class names do not permit its actions to be copied
to another position or history.

The standalone trainer is intentionally not changed in this approval-only
commit. It must be synchronized together with the complete approved BTN-vs-BB
strategy in the later publication pass.

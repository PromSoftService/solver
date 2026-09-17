# BB response to BTN c-bet: approved human simplification

## 1. Scope and source

This document records the user-approved teaching strategy for
`STU005 / 03_BB_AFTER_CBET`: after
`BB CHECK -> BTN BET 1/2`, BB chooses FOLD, CALL or native-60 RAISE.

The numerical source is the completed combo-level export
`20260915-055252Z/03_BB_AFTER_CBET/combos.csv`: 150,051 rows,
of which 150,041 have positive reach. All 286 boards passed validation.
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
| Two pair+ | C/R | C/R | R | R | R | R |
| Overpair | — | — | — | — | — | R |
| Top pair | C | C | C | C | C | C |
| Underpair | — | — | C | C | C | C |
| Second pair | C | C | C | C | C | C |
| Weak pair | — | — | C | C | C | C |
| Third pair | BDFD | BDFD | C | C | C | C |
| Low pocket pair | F | F | F | F | F | F |
| OESD | C | C | R | R/C | R/C | R/C |
| Gutshot | PAIR | PAIR | C | C | C/R | C/R |
| 2 overcards + BDFD | — | — | — | — | R | C/R |
| Air | F | F | F | F | F | F |

`C/R` and `R/C` are exact 50/50 randomizers; order records the
solver-majority action.

`BDFD` means CALL with a backdoor flush draw and FOLD without one.
`PAIR` means CALL when the Gutshot also contains any made pair and FOLD
without a made pair. Both are deterministic observable selectors, not
randomizers. `—` means the category is absent at that class.

The selector split was checked directly: dense-Broadway Third pair with BDFD
calls about 96% on both ABB and BBB, while without BDFD it folds 100% on ABB
and about 99.3% on BBB. Paired Gutshots call about 95.6% on ABB and 86.3% on
BBB; the `PAIR` rule deliberately rejects the less stable unpaired subgroup.

The six classes are mutually exclusive and exhaustive. Their board counts are
6 / 4 / 60 / 96 / 64 / 56, totaling all 286 BRD001 flops.

## 3. Strategic structure

Ordinary pairs form the CALL core. Low pocket pairs and Air always fold.
Strong value transitions from a protected `C/R` on dense Broadway flops to
pure RAISE on the remaining structures.

OESD follows a monotone pressure ladder: CALL on `ABB/BBB`, pure RAISE on
`Axx`, then `R/C` from K/Q-high downward. Gutshot is deliberately calmer:
the `PAIR` filter on `ABB/BBB`, pure CALL on `Axx` and `K/Qxx`, then
`C/R` on `J/Txx` and low boards.

Third pair uses one clean transition: it needs BDFD on `ABB/BBB`, then
always calls. Two overcards plus BDFD enter only where the category exists:
pure RAISE on `J/Txx`, then `C/R` on `[9-2]xx`.

The table deliberately over-folds weak holdings and under-raises relative to
the solver. That bias is accepted to avoid over-calling and to keep the
check-raise range concentrated in strong value and direct draws.

## 4. Reproduced audit

| Metric | Solver | Candidate | Delta |
|---|---:|---:|---:|
| FOLD | 43.1372% | 50.5559% | +7.4188 pp |
| CALL | 45.7067% | 41.2229% | -4.4837 pp |
| RAISE | 11.1562% | 8.2211% | -2.9350 pp |
| Continue | 56.8628% | 49.4441% | -7.4188 pp |

- mean reach-weighted local source loss: 0.017993 bb;
- mean local oracle regret: 0.019105 bb;
- oracle-regret P95 / P99 / P99.9: 0.069160 / 0.561649 / 1.061952 bb;
- reach above 0.50 / 1.00 bb oracle regret: 1.2114% / 0.1343%;
- maximum single-combo oracle regret: 1.705230 bb.

The worst concentration is `Air / J/Txx`: on `Js 7h 2d`, several unmade
ace-high combinations such as `AcQd` are forced to FOLD even though CALL is
the best saved pure action. This is the main visible cost of the chosen
anti-overcall bias.

The continuation deviation remains below the 10 percentage-point defense
guardrail and mean source loss remains below 0.020 bb. P99 is above the
preferred 0.50 bb line, so the tail is an explicitly reviewed cost rather
than an unnoticed pass.

## 5. Approval and scope boundary

All six classes are reachable through the approved upstream BTN c-bet model;
none of these columns is documentation-only on the normal training path.

The user approved this exact six-column candidate on 2026-09-17 after the
defense display order was corrected to keep `ABB` and `BBB` adjacent.

Approval is branch-specific. Identical class names do not permit actions to be
copied to UTG-vs-BB, UTG-vs-BTN or another BTN-vs-BB branch. Any later change
requires a fresh frequency, subgroup-composition and fixed-opponent EV audit
from this branch's tracked combo data.

The standalone trainer is intentionally not changed in this documentation
commit. It must be synchronized only when the approved BTN-vs-BB tables are
published together.

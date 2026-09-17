# BTN response to BB donk: approved human simplification

## 1. Scope and source

This document records the user-approved teaching strategy for
`STU005 / 05_BTN_AFTER_DONK`: after `BB DONK BET 1/2`, BTN chooses FOLD,
CALL or native-60 RAISE.

The numerical source is the completed combo-level export
`20260915-055252Z/05_BTN_AFTER_DONK/combos.csv`: 153,604 positive-reach rows.
All 286 boards passed validation. The solver, production generator, canonical
workbook and source dataset are unchanged. This table is a manual teaching
layer and is not generated or consumed by repository code.

The shared hand priority is mandatory:

`OESD -> Gutshot -> made hand -> 2 overcards + BDFD -> Air`.

## 2. Approved table

Defense/response display order is
`ABB -> BBB -> Axx -> K/Qxx -> J/Txx -> [9-2]xx`.

| Hand category | ABB | BBB | Axx | K/Qxx | J/Txx | [9-2]xx |
|---|---:|---:|---:|---:|---:|---:|
| Two pair+ | C/R | C/R | C/R | C/R | C/R | C/R |
| Overpair | — | — | — | C | C | C |
| Top pair | C | C | C | C | C | C |
| Underpair | — | — | C | C | C | C |
| Second pair | C | C | C | C | C | C |
| Weak pair | — | — | C | C | C | C |
| Third pair | BDFD | BDFD | C | C | C | C |
| Low pocket pair | F | F | F | F | F | F |
| OESD | C/R | C/R | C/R | C/R | C/R | C/R |
| Gutshot | C/R | C/R | C/R | C/R | C/R | C/R |
| 2 overcards + BDFD | — | — | — | C | C | C |
| Air | F | F | BDFD | BDFD | BDFD | BDFD |

`C/R` is an exact 50/50 CALL/RAISE mix. `BDFD` means CALL with a
backdoor flush draw and FOLD without one. It is a deterministic observable
selector, not a randomizer. `—` means the category is absent at that class.

The six classes contain 6 / 4 / 60 / 96 / 64 / 56 boards and cover all
286 BRD001 flops exactly once.

## 3. Strategic structure

Two pair+, OESD and Gutshot form the uniform 50/50 raising core. Ordinary
pairs call; Low pocket pair folds. Dense-Broadway Third pair needs BDFD,
while the same row calls from Axx downward.

Air is deliberately conservative. It folds on `ABB/BBB` and continues only
with BDFD from Axx downward. Testing pure FOLD for Air increased mean local
source loss to about 0.0316 bb; adding BDFD progressively through Axx and
K/Qxx reduced the error, and the approved all-lower-class BDFD rule brought
it back to the accepted range without a rank- or suit-specific micro-program.

Pure CALL for Gutshot would lower mean local source loss to about 0.0136 bb,
but would collapse the candidate raise frequency to roughly 4.19%. The
approved `C/R` keeps a transparent direct-draw raising range and remains
inside the branch-specific raise-deviation boundary.

## 4. Reproduced audit

| Metric | Solver | Candidate | Delta |
|---|---:|---:|---:|
| FOLD | 29.2521% | 38.8037% | +9.5516 pp |
| CALL | 54.2480% | 49.2678% | -4.9802 pp |
| RAISE | 16.4999% | 11.9284% | -4.5714 pp |

- branch reach relative to the solver flop root: 2.4889%;
- mean reach-weighted local source loss: 0.017220 bb;
- root-normalized source loss: 0.000429 bb;
- mean local oracle regret: 0.041644 bb;
- root-normalized oracle regret: 0.001036 bb;
- oracle-regret P95 / P99 / P99.9: 0.248375 / 0.599497 / 1.110860 bb;
- reach above 0.50 / 1.00 bb oracle regret: 1.5435% / 0.1536%;
- maximum single-combo oracle regret: 5.167240 bb.

The candidate deliberately over-folds and under-raises weak holdings. The
largest local tail is a rare `Third pair / BBB` no-BDFD combination forced to
FOLD; several other large outliers are unmade ace-high Air without BDFD on
J/T-high boards. These tails are recorded rather than hidden by additional
micro-rules.

## 5. Reachability and trainer exception

Under the approved baseline `5.4.1 BB DONK 1/2`, BB checks the entire range,
so this branch has zero reach against the teaching baseline. It is retained
for a different purpose: training BTN against human opponents who may donk
despite the solver and baseline strategy.

This is an explicit exception to normal-path generation. The standalone
trainer must offer `5.4.5 BB DONK 1/2 -> BTN RESPONSE` on **all six flop
classes**, not only as a documentation table. It must label or internally
treat the history as opponent-deviation training so the exception does not
change `5.4.1`, invent a solver donk frequency or make other off-policy
branches automatically reachable.

The solver branch-reach value above describes the solved source tree and is
reported only for audit normalization. It is not the probability with which
the human-deviation exercise should be sampled.

## 6. Approval and scope boundary

The user approved this exact six-column candidate and the all-flop trainer
exception on 2026-09-17. Approval is branch-specific: identical class names
do not permit its actions to be copied to another position or history.

The standalone trainer file is intentionally not changed in this
approval-only commit. The mandatory all-six-class exercise must be implemented
with the complete approved BTN-vs-BB strategy in the next publication pass.

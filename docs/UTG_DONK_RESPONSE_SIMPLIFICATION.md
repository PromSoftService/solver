# UTG response to BB donk: approved manual simplification

## Scope and provenance

This is the user-approved human table for `STU002 / 05_UTG_AFTER_DONK`:
after `BB DONK 1/2`, UTG chooses FOLD, CALL or native-60 RAISE.

The numerical source is the tracked aggregate branch export
`datasets/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/05_UTG_AFTER_DONK/20260909-003948Z/combos.csv`.
The audit used 80,553 positive-reach combo rows and all 286 BRD001 boards.
No GPU solve was launched.

The table is a manually reviewed teaching artifact. The production generator
still creates only the canonical solver-frequency workbook; it neither reads
nor writes this table.

## Approved table

| Hand category | ABB / BBB | Axx / Bxx | [9-2]xx |
|---|---:|---:|---:|
| Two pair+ | C/R | C/R | C/R |
| Overpair | - | C | C |
| Top pair | F | C | C/R |
| Underpair | - | C | C |
| Second pair | F | C | C |
| Weak pair | - | C | C |
| Third pair | F | C | C |
| Low pocket pair | F | F | C |
| OESD | C/R | C/R | C/R |
| Gutshot | C/R | C/R | C/R |
| 2 overcards + BDFD | - | C | C |
| Air | F | BDFD | BDFD |

`C/R` is an exact 50/50 CALL/RAISE randomizer. `BDFD` means CALL with a
backdoor flush draw, otherwise FOLD. Draw rows retain priority over made hands.

The partition is mutually exclusive and exhaustive: `ABB / BBB` has 10
boards, non-ABB/BBB `Axx / Bxx` has 220, and `[9-2]xx` has 56.

## How the decision was made

The primary analysis rebuilt the hand classifier from raw cards with the shared
priority OESD, Gutshot, made hand, two overcards plus BDFD, then Air. It compared
pure F/C/R and exact 50/50 policies per concrete combo.

The five-column teaching table was tested first. The three-column candidate
merged paired Broadway boards, unpaired A/B-high boards, and low boards. Hidden
cell-specific selectors and rare solver raises with pairs or Air were rejected.
The intended human raise range is strong value plus OESD and Gutshot; top pair
adds value raises only on low boards.

GPT-6 Astra received the reproduced totals, row composition, EV measures and
tails as an independent critic. It accepted the same candidate, identified
over-folded Air as the main distortion, and found no single supported simple
change that improved the result. Its conclusion was not used as data; all
reported numbers below come from the tracked export.

## Reproduced audit

| Metric | Solver | Old five-column table | Approved table |
|---|---:|---:|---:|
| FOLD | 28.0434% | 29.0199% | 37.2857% |
| CALL | 59.0276% | 56.0834% | 52.7215% |
| RAISE | 12.9290% | 14.8967% | 9.9928% |
| Root source loss | - | 0.011530 bb | 0.003877 bb |
| Root clipped loss | - | 0.014256 bb | 0.008518 bb |
| Local oracle P99 | - | 4.0315 bb | 3.4875 bb |

The accepted frequency deltas versus solver are +9.2423 pp FOLD, -6.3061 pp
CALL and -2.9362 pp RAISE. They stay within the branch's agreed approximate
10 pp overall-frequency and 0.020 bb root-loss limits.

The deliberate distortion is concentrated in Air: the candidate folds 90.83%
of Air reach versus 65.73% for solver. It also raises OESD and Gutshot more
often while omitting rare raises with overpairs, second/third pairs,
two-overcards-plus-BDFD and Air. Aggregate frequencies therefore do not prove
robustness against an adapting opponent.

These are fixed-opponent local EV/regret checks, not exploitability. The simpler
table was accepted because its remaining errors are explicit and teachable, and
because it improved both root-loss measures and the P99 tail versus the former
five-column teaching table.

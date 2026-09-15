# BB defense simplification: reproducible worked example

## 1. Scope and source of truth

This document records the approved human simplification for
`STU002 / 03_BB_AFTER_CBET`: BB responds after
`BB CHECK -> UTG BET 1/2` with FOLD, CALL or native-60 RAISE.

The only numerical source is the tracked branch export
`20260908-220332Z/combos.csv`. It contains 106,381 rows; the audit uses
106,308 positive-reach rows. No solver run is needed to reproduce the result.

The canonical ten-column workbook remains untouched. The human candidate is a
manual interpretation layer: the analyst inspects the tracked solver export,
checks a proposed simplification and records the user-approved Markdown table.
No production script generates, consumes or promotes this human table. The
tracked `analysis/human-5` directory is an earlier rejected five-class audit
retained only as historical evidence; it is not the source of truth for the
approved table.

The shared hand classifier priority is mandatory:

1. OESD;
2. Gutshot;
3. made hand;
4. two overcards plus BDFD;
5. Air.

A pair inside OESD or Gutshot remains in the draw row.

## 2. How the table evolved

The first detailed review used eight flop classes. It exposed real
discontinuities on `ABB`, `BBB`, third pairs, direct draws and BDFD, but the
result was too large to learn.

The next primary analysis tested a five-class partition:

- `ABB`;
- `Axx`, excluding `ABB`;
- `BBB`;
- `Bxx`, excluding `BBB`;
- `[9-2]xx`.

Pure F/C/R and exact 50/50 C/R policies were evaluated per concrete combo.
Conditional selectors were tested separately. Global frequencies were never
accepted without board-family, made-pair-inside-draw, BDFD and loss-tail checks.

GPT-6 Astra then received the branch provenance, exact class definitions,
candidate metrics, worst cells and the user's complexity limit. Astra acted as
an independent critic. Its meaningful alternative was reproduced locally
rather than copied. For this branch the user selected pure CALL for
`Second pair / Bxx`, avoiding rare solver raises that did not justify another
human rule.

The user then fixed the strategic model for this defensive table:

- the learnable check-raise range is strong value plus OESD and Gutshot;
- rare solver raises with pairs or Air are deliberately omitted;
- total RAISE frequency is still audited, but matching solver raise-range
  composition is not a rejection condition by itself;
- C/R and R/C remain exact 50/50 randomizers where preserving check-raise
  volume matters;
- CALL/FOLD is not randomized. A `C/F` rule must use one observable,
  monotone strength boundary for the whole hand row;
- cell-specific hidden selectors are forbidden.

A global Weak-pair strength selector looked good in aggregate but failed the
subgroup test: it called bad A-high weak pairs and folded good low-board weak
pairs. The solver pattern was approximately 95% FOLD on Axx, 69% FOLD on Bxx
and 86% CALL on low boards. Therefore `F / F / C` was retained.

Finally `ABB` and `BBB` were merged. Both are dense Broadway structures
that favour the UTG range and their action vectors coincide after one
observable Gutshot selector: `PAIR` means CALL with a made pair inside the
Gutshot, otherwise FOLD. This merge improved, rather than merely preserved,
the EV and tail audit.

For the final teaching display, `Axx` and `Bxx` were also merged into
`Axx / Bxx`. Their approved action vectors are identical in every hand row,
so this is an exact presentation merge: it changes neither the combo policy
nor any audit metric.

## 3. Approved table

| Hand category | ABB / BBB | Axx / Bxx | [9-2]xx |
|---|---:|---:|---:|
| Two pair+ | C/R | R | R |
| Overpair | — | C | C |
| Top pair | C | C | C |
| Underpair | — | C | C |
| Second pair | F | C | C |
| Weak pair | — | F | C |
| Third pair | F | C | C |
| Low pocket pair | F | F | F |
| OESD | C | R/C | R/C |
| Gutshot | PAIR | C/R | C/R |
| 2 overcards + BDFD | — | C | C |
| Air | F | F | F |

`PAIR`: CALL with any made pair inside the Gutshot; otherwise FOLD.
`C/R` and `R/C`: the same exact 50/50 randomizer; order records solver
majority.

The displayed partition is mutually exclusive and exhaustive:
`ABB / BBB` 10 boards, `Axx / Bxx` 220 and `[9-2]xx` 56;
the counts sum to all 286 BRD001 boards. Internally, the audit may still split
the middle class into 60 Axx and 160 Bxx boards for subgroup checks.

## 4. Branch-specific acceptance guardrails

The two core working limits agreed for this defense are:

- absolute deviation of total continuation frequency no more than 10
  percentage points;
- mean clipped fixed-opponent source loss no more than 0.020 bb.

The audit also uses warning limits, not universal generator thresholds:

- absolute RAISE-frequency deviation no more than 5 percentage points;
- mean oracle regret no more than 0.025 bb;
- P99 at or below 0.50 bb is preferred; 0.50-1.00 bb requires review;
- reach above 0.50 bb no more than 1%; reach above 1.00 bb no more than 0.3%.

Passing totals never overrides a subgroup veto. Reject error cancellation,
wrong draw/made-hand composition, non-observable selectors, and concentrated
losses in a strategically important board family.

These are local EV checks against the stored solved opponent strategy. They are
not exploitability or a proof that the simplification remains equilibrium-safe.

## 5. Reproduced final audit

| Metric | Solver | Candidate | Delta |
|---|---:|---:|---:|
| FOLD | 47.8993% | 51.2297% | +3.3303 pp |
| CALL | 39.0930% | 37.9128% | -1.1802 pp |
| RAISE | 13.0076% | 10.8575% | -2.1501 pp |
| Continue | 52.1007% | 48.7703% | -3.3303 pp |

- mean source-mix loss: 0.013265 bb;
- mean clipped source loss: 0.013848 bb;
- mean oracle regret: 0.015272 bb;
- P95 / P99 / P99.9: 0.033336 / 0.431487 / 1.162140 bb;
- reach above 0.50 / 1.00 bb: 0.8767% / 0.2463%;
- maximum single-combo oracle regret: 1.760492 bb.

Against the immediately preceding manual five-class version, merging
`ABB/BBB` with the shared `PAIR` selector reduced mean source loss from
0.013751 to 0.013265 bb and P99 from 0.449442 to 0.431487 bb.

## 6. Repetition protocol

1. Load the exact tracked branch `combos.csv` and rerun the shared classifier.
2. Start from the smallest familiar exhaustive flop partition.
3. Choose coarse actions from solver frequencies; use EV only as a veto.
4. Build the human check-raise range from value plus direct draws.
5. Enumerate pure actions and exact 50/50 mixes.
6. Permit only observable, row-wide selectors; audit both sides separately.
7. Audit totals, board families, hand rows, draw subtypes, composition and tails.
8. Send a compact evidence package to Astra for independent criticism.
9. Reproduce every accepted Astra proposal locally from tracked data.
10. Obtain user approval and record the exact Markdown table, supporting
    evidence, metrics and decision in documentation. Leave the production
    generator and canonical solver workbook unchanged.

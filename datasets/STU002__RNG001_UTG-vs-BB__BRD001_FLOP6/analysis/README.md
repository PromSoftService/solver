# STU002 active strategy outputs

This directory contains the reproducible machine-readable strategy, validation
audits and one human workbook for `STU002__RNG001_UTG-vs-BB__BRD001_FLOP6`.

Human workbook:

- `STU002_flop_strategy.xlsx` — 12 hand rows by the final 10 flop categories.

Machine-readable outputs:

- `strategy-10/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the numeric strategy directly from tracked solver combo frequencies:

```text
python scripts/generate-flop-strategies.py STU002__RNG001_UTG-vs-BB__BRD001_FLOP6
```

Build the workbook with the approved colors and layout:

```text
node scripts/build-flop-workbooks.mjs STU002__RNG001_UTG-vs-BB__BRD001_FLOP6
```

`BDFD` in a cell means fold without a backdoor flush draw and call with one.
The full method and range provenance are in `docs/FLOP_STRATEGY_WORKFLOW.md`.
Rejected horizontal smoothing experiments remain only in Git history.

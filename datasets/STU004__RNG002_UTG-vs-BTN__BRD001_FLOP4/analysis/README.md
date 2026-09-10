# STU004 active strategy outputs

This directory contains the reproducible machine-readable strategy, validation
audits and the two human workbooks for `STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4`.

Human workbooks:

- `STU004_simplified_flop_strategy.xlsx` — 12 hand rows by B13;
- `STU004_strategy_8_categories.xlsx` — the same hand rows by eight broader
  flop categories.

Machine-readable outputs:

- `strategy-13/`;
- `strategy-8/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the numeric strategy directly from the tracked solver combo frequencies:

```text
python scripts/generate-flop-strategies.py STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4
```

Build the two workbooks with the approved colors and layout:

```text
node scripts/build-flop-workbooks.mjs STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4
```

The full method and range provenance are in `docs/FLOP_STRATEGY_WORKFLOW.md`.
Rejected horizontal smoothing experiments remain only in Git history.

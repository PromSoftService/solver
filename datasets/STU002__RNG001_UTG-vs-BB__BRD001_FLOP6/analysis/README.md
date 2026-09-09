# STU002 active strategy outputs

This directory intentionally contains only the current reproducible strategy
standard and its audits.

Human workbooks:

- `STU002_simplified_flop_strategy.xlsx` — 11 hand rows by B13;
- `STU002_strategy_8_categories.xlsx` — the same hand rows by eight broader
  flop categories.

Machine-readable outputs:

- `strategy-13/`;
- `strategy-8/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the numeric tables with:

```text
python scripts/analyze-stu002.py
python scripts/generate-stu002-strategies.py
```

Build the workbooks with:

```text
node scripts/build-stu002-workbooks.mjs
```

The full frozen method and range provenance are in
`docs/STU002_STRATEGY_WORKFLOW.md`. Rejected horizontal-smoothing experiments
are available only in Git history and must not be treated as current outputs.

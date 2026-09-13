# STU004 active strategy outputs

This directory contains the reproducible machine-readable strategy, validation
audits and one human workbook for `STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4`.

Human workbook:

- `STU004_flop_strategy.xlsx` — 12 hand rows by the final 10 flop categories.

Machine-readable outputs:

- `strategy-10/`;
- `SOURCE_VALIDATION.json`;
- `FINAL_VALIDATION.json`;
- `FLOP_GROUPS.json`.

Rebuild the machine-readable strategy, audits and approved workbook directly
from tracked solver combo frequencies:

```text
python scripts/generate-flop-strategies.py STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4
```

The same command writes the workbook with the approved colors and layout using
local Python and `openpyxl`; Codex and `@oai/artifact-tool` are not required.

`BDFD` in a cell means fold without a backdoor flush draw and call with one.
The full method and range provenance are in `docs/FLOP_STRATEGY_WORKFLOW.md`.
Rejected horizontal smoothing experiments remain only in Git history.

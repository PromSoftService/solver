# Strategy scripts

Supported entry point:

```text
python scripts/generate-flop-strategies.py <study-directory> [--run <run-name>]
```

The entry point validates tracked datasets and delegates to two cohesive shared modules:

- `flop_strategy.py`: board/hand classification, combo loading and validation;
- `flop_workbook.py`: deterministic workbook creation and XLSX verification.

`generate-study-config.mjs` reproducibly builds the STU004 and STU005 solver configs from tracked ranges. Pass a study ID or omit arguments to rebuild every supported config. The PowerShell files launch study branches and do not implement strategy analysis.

There is no active STU003 generator and no human-strategy generator. The supported Python path only converts tracked solver data into the canonical solver-frequency Excel workbook. It never selects teaching flop classes, applies human actions, consumes an Astra review or promotes a Markdown table.

Human simplification is performed manually after workbook generation under `docs/HUMAN_STRATEGY_SIMPLIFICATION.md`. Branch-specific analysis may use temporary local calculations, but no study-specific human-table generator is kept in `scripts/`.

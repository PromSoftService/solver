# Strategy scripts

Supported entry point:

```text
python scripts/generate-flop-strategies.py <study-directory> [--run <run-name>]
```

The entry point validates tracked datasets and delegates to two cohesive shared modules:

- `flop_strategy.py`: board/hand classification, combo loading and validation;
- `flop_workbook.py`: deterministic workbook creation and XLSX verification.

`generate-study-config.mjs` reproducibly builds the STU004 and STU005 solver configs from tracked ranges. Pass a study ID or omit arguments to rebuild every supported config. The PowerShell files launch study branches and do not implement strategy analysis.

There is no active STU003 generator and no separate human-candidate workbook generator. Human candidates follow `docs/HUMAN_STRATEGY_SIMPLIFICATION.md` and become generated workbooks only after explicit approval.

`analyze-human-bb-response.py` is a deliberately branch-specific audit for the separate STU002 five-class BB-versus-c-bet candidate. It reads the tracked combo/action EV export and reproduces `analysis/human-5/03_BB_AFTER_CBET`; it never launches the solver or changes the canonical workbook.

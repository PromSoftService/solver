# TexasSolverGPU batch runner

Windows batch automation for **TexasSolverGPU v0.2.0 x64**. It keeps the original CUDA/GPU engine and uses only verified WebView2 bridge methods.

## Production model

For each flop the runner:

- launches `TexasSolverGpu_131.exe` with the host window suppressed;
- initializes the configured ranges, pot, stack and betting tree;
- performs one GPU solve and waits for convergence;
- applies the configured action history;
- exports one selected current-street decision with `solver.export.currentStreet`;
- writes native JSON, combo JSON/CSV, a bridge transcript and run metadata.

This is the supported stock workflow. The runner does **not** claim to save or reload the complete solved postflop tree. To collect another branch later, run a separate job with another `runner.decisionNode`.

## Quick start

Keep this repository beside `TexasSolverGpu-v0.2.0-windows-x64`, then run:

```powershell
.\tsgpu-batch.cmd .\example\config.json .\example\boards.txt .\output\example-five-flops
```

The example contains five flops and one IP flop bet size, 33%. Its `runner` block selects `BB_RESPONSE` and verifies the expected native amounts: bet 18, raise 73.

Command-line options override matching `runner` values from JSON. The relevant settings are:

```json
{
  "runner": {
    "maxIterations": 1000,
    "targetExploitability": 0.5,
    "decisionNode": "BB_RESPONSE",
    "expectedBetAmount": 18,
    "expectedRaiseAmount": 73
  }
}
```

Supported UTG-vs-BB flop presets are `BB_FIRST`, `UTG_CBET`, `BB_RESPONSE`,
`UTG_VS_CHECK_RAISE`, `UTG_VS_DONK`, and `BB_VS_DONK_RAISE`. Existing
UTG-vs-BTN presets remain `UTG_OOP_CBET`, `BTN_RESPONSE`, `BTN_STAB`, and
`UTG_RESPONSE`. `expectedBetAmount` and `expectedRaiseAmount` are safety
checks; use `0` to disable a check.

## Output

Each numbered board directory contains `run.json`, `node.raw.json`, `combos.json`, `combos.csv`, and `bridge-transcript.jsonl`. The output root contains `batch-summary.json` and `batch-summary.csv`.

`-Resume` reuses only boards with both `run.json` and `combos.json` and verifies that the decision preset matches.

See `example/README.md`, `docs/BASELINE.md`, `docs/BRIDGE_SCHEMA.md`, and `docs/HISTORY.md`.

## Active studies

`studies/STU001__RNG001_UTG-vs-BB__5FLOP_50-50/` is the first reproducible
performance study. It uses RNG001, five canonical BRD001 flops, one 50% normal
bet size on flop and turn, and writes raw output locally under `output/` plus
compact tracked reports under `datasets/`.

`studies/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/` defines six independent
stock jobs that cover the complete normal-action UTG-vs-BB flop interaction
over BRD001. Each board/branch still performs its own solve and exactly one
current-street export.

Its completed compact datasets now feed two approved human-strategy tables:
13 hand rows by B13 and the same hand rows by eight broader flop categories.
The exact range provenance, classifiers, aggregation rule, EV audit and rebuild
commands are fixed in `docs/STU002_STRATEGY_WORKFLOW.md`.

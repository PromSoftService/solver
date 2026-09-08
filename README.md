# TexasSolverGPU batch runner

Windows batch automation for **TexasSolverGPU v0.2.0 x64**. The runner preserves the proven v015 WebView2/GPU solve pipeline and adds complete postflop solved-tree persistence.

## What it does

For every board the runner:

- launches `TexasSolverGpu_131.exe` with its window suppressed;
- initializes and allocates the configured postflop tree;
- performs one GPU solve and waits for convergence;
- exports the requested current decision node and combo CSV/JSON;
- saves every reachable flop/turn/river native strategy fragment into one complete archive;
- records solver, config, runner and archive hashes for reproducibility.

No poker solver is reimplemented. No guessed bridge method is called.

## Command

Place this repository next to `TexasSolverGpu-v0.2.0-windows-x64`, then run:

```powershell
.\tsgpu-batch.cmd config.json boards.txt output\
```

`config.json` supplies tree/ranges/stack/pot/sizings plus `runner.maxIterations` and `runner.targetExploitability`. `boards.txt` contains one flop per non-comment line and has no runner-imposed 20-board limit.

Full-tree export is enabled by default. `-SkipFullTreeExport` exists only for legacy selected-node runs. `-Resume` skips a completed board only when its complete archive is present.

## One-board smoke

```powershell
.\tsgpu-batch.cmd .\smoke\CFG001-one-board.json .\smoke\boards.txt .\output\smoke -ExpectedBetAmount 18 -ExpectedRaiseAmount 73
```

Offline deep validation, after the solver process has closed:

```powershell
python .\scripts\inspect-full-tree.py .\output\smoke\0001_6s_As_8c\full-tree.tsgpu.zip --deep
```

## Per-board output

- `full-tree.tsgpu.zip` — complete native flop/turn/river archive;
- `full-tree.manifest.json` — archive hash, size and completion totals;
- `run.json` — solve/current-node/full-tree metadata;
- `node.raw.json` — selected native current-street node;
- `combos.json`, `combos.csv` — selected-node combo report;
- `bridge-transcript.jsonl` — exact bridge calls;
- batch root `batch-summary.json` and `batch-summary.csv`.

See `docs/FULL_TREE_EXPORT.md`, `docs/BRIDGE_SCHEMA.md`, `docs/BASELINE.md`, and `docs/HISTORY.md`.

The repository intentionally contains no generated study datasets or solver binaries.

# TexasSolverGPU runner development baseline

This repository is a clean engineering baseline for automating **TexasSolverGPU v0.2.0 Windows x64**. It does not contain poker-study results.

## Current state

The active runner is the last proven `v015-production` implementation. It can reliably:

- launch `TexasSolverGpu_131.exe` headlessly;
- connect through the WebView2 bridge;
- initialize and allocate the configured postflop tree;
- solve it and poll status;
- navigate history/actions;
- export the selected current-street strategy node.

It **does not yet persist the complete solved tree**. That is the next runner-development task.

A later experimental `v020` generation attempted to discover a full-tree exporter by probing invented/plausible endpoint names. That approach was rejected and is not present in the baseline.

## Repository contents

- `tsgpu-worker.ps1`, `tsgpu-batch.ps1`, `tsgpu-batch.cmd` — proven v015 runner core;
- `ranges/` — source RNG001 (UTG vs BB) and RNG002 (UTG vs BTN) ranges;
- `boards/` — BRD001, 286 canonical unpaired-rainbow flops;
- `smoke/` — one-board runner-development fixture;
- `scripts/Range-Utils.ps1` — source-range utility;
- `docs/` — baseline, verified bridge facts and historical record;
- `.github/workflows/runner-check.yml` — static Windows validation only.

There are intentionally no `datasets/`, `analysis/`, `results/`, `studies/`, `configs/` or `tools/` directories in active `main`.

## Smoke command

From the repository root, with the solver available through `TSGPU_SOLVER_EXE` or in the known adjacent location:

```powershell
.\tsgpu-batch.cmd .\smoke\CFG001-one-board.json .\smoke\boards.txt .\output\smoke
```

This exercises the proven current-node runner only. It is **not** a full-tree persistence test.

## Development objective

The next implementation must discover and use the real TexasSolverGPU mechanism for saving/exporting the complete solved strategy tree. Prove that mechanism on one smoke board before any large study is created.

See `AGENTS.md`, `docs/BASELINE.md`, `docs/BRIDGE_SCHEMA.md`, and `docs/HISTORY.md`.

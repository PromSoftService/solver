# Clean runner-development baseline

## Baseline commit intent

This tree is intentionally **not** a poker-research state. It is a clean engineering starting point for the runner.

The active implementation is the proven `v015-production` solve/current-street-export core copied from historical commit:

`bec0b758fe7957a45d028f1adaa2a5252ff0598a`

That old commit contained many datasets, analyses and study launchers. None of those are part of this baseline.

## Proven behavior

`tsgpu-worker.ps1` has been proven on the user's Windows/NVIDIA machine to:

- launch `TexasSolverGpu_131.exe`;
- suppress the host window;
- connect to the WebView2 bridge;
- `solver.init`;
- `solver.allocate`;
- start and monitor GPU solves;
- apply action history;
- inspect actions;
- export a selected current-street strategy node;
- write per-node combo strategy/EV metadata.

`tsgpu-batch.ps1` has been proven as the multi-board wrapper around that worker.

## Explicitly not implemented

**Complete solved-tree persistence is not implemented.**

The baseline does not contain:

- a verified full-tree save/export call;
- viewer-compatible complete-tree persistence;
- automatic traversal/export of all turn/river nodes;
- full-tree studies;
- automatic study-result commits.

A previous `v020` experiment guessed possible full-tree endpoint names and validated returned JSON heuristically. That was rejected as a development method and removed.

## Source inputs retained

### Ranges

- RNG001 — UTG open 2.5bb -> BB call;
- RNG002 — UTG open 2.5bb -> BTN call.

These are source inputs copied from the TexasSolverGPU bundled 6-max range library and are not research results.

### Boards

- BRD001 — 286 canonical unpaired-rainbow flops.

### Smoke fixture

`smoke/CFG001-one-board.json` and `smoke/boards.txt` are retained only to reproduce the proven runner on one small input while developing the exporter. They are not an active study definition.

## Directory policy

Active `main` deliberately has no:

- `datasets/`;
- `analysis/`;
- `results/`;
- `studies/`;
- `configs/`;
- `tools/`.

Historical material remains in Git history and can be inspected without restoring it to active `main`.

## Next engineering milestone

Identify the real complete-strategy save/export mechanism used by TexasSolverGPU v0.2.0 and prove it on one smoke board. Only after that should a new study format or batch-output contract be designed.

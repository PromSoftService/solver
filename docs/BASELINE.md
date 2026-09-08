# Production runner baseline

## Core lineage

The startup/solve/current-node core remains the proven `v015-production` implementation copied from historical commit:

`bec0b758fe7957a45d028f1adaa2a5252ff0598a`

The full-tree work adds a post-solve persistence layer. It does not replace the GPU solver, change poker abstraction, or alter init/allocate/start/status/window-suppression behavior.

## Proven behavior

On the user's Windows/NVIDIA host the runner has proven:

- headless launch of `TexasSolverGpu_131.exe`;
- WebView2 bridge connection and token handling;
- `solver.init`, `solver.allocate`, one GPU solve and status polling;
- action-history navigation and selected-node combo export;
- native flop → turn → river export from the same solved process;
- ZIP persistence and independent offline parsing without a solver process.

Full-tree persistence uses only confirmed `solver.history.apply`, `solver.cards.possible`, and `solver.export.currentStreet` calls. The archive is marked complete only after all indexed chance children are saved.

## Source inputs retained

- RNG001 — UTG open 2.5bb → BB call;
- RNG002 — UTG open 2.5bb → BTN call;
- BRD001 — 286 canonical unpaired-rainbow flops;
- `smoke/CFG001-one-board.json` and `smoke/boards.txt` — one-board development fixture.

These are inputs, not generated research results.

## Directory policy

Active `main` deliberately has no generated `datasets/`, `analysis/`, `results/`, `studies/`, `configs/`, or `tools/` directories. Runtime output goes under the ignored `output/` or `_diagnostics/` directories.

## Production contract

`tsgpu-batch.cmd config.json boards.txt output\` solves each board once and, by default, requires `full-tree.tsgpu.zip` before recording that board as complete. A resume operation does not accept old selected-node-only output as a completed full-tree job.

The archive preserves exact config, solver SHA256, runner version/commit/source hashes, solve parameters, native fragment hashes, total size and timestamps. See `FULL_TREE_EXPORT.md`.

## Known operational risks

- Complete export is substantially larger and slower than selected-node export.
- The in-memory solved state cannot be restored after a crash because v0.2.0 exposes no solved-state loader; a failed board must be solved again.
- Native schema compatibility is tied to TexasSolverGPU v0.2.0 and must be checked through archive metadata and the offline validator.

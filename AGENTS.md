# Mandatory instructions for PromSoftService/solver

Remote `main` is the source of truth. Read this file before changing the repository.

## Purpose

This repo is a development workspace around the original `TexasSolverGpu_131.exe` from TexasSolverGPU v0.2.0 Windows x64. Do not replace or reimplement the solver unless the user explicitly asks.

The immediate engineering task is to make the runner persist the **complete solved postflop strategy tree** by using the real mechanism exposed by the installed TexasSolverGPU runtime/frontend. Strategy research is intentionally out of scope until that persistence mechanism is proven.

## Baseline status

The clean baseline is intentionally small:

- `tsgpu-worker.ps1` — proven `v015-production` worker from historical commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`;
- `tsgpu-batch.ps1` and `tsgpu-batch.cmd` — proven batch shell from the same state;
- `scripts/Range-Utils.ps1` — source-range expansion utility;
- `ranges/` — RNG001 and RNG002 source inputs;
- `boards/BRD001...txt` — 286 canonical unpaired-rainbow flop inputs;
- `smoke/` — one-board development fixture only;
- documentation and one static Windows CI workflow.

`v015` reliably starts the solver, hides the host window, connects to the WebView2 bridge, initializes/allocates, solves, polls status, applies history and exports a selected current-street node.

**Complete solved-tree persistence is NOT implemented in the baseline.** Do not claim otherwise.

## Full-tree development rule

Do not guess API names such as `solver.export.fullTree`, `solver.export.fullStrategy`, `solver.dump.strategy`, etc. A previous experiment did that and was discarded.

Before implementing full-tree persistence:

1. inspect the actual installed runtime/frontend behavior;
2. identify the real native/bridge/frontend mechanism used to save or dump a complete strategy;
3. prove it on exactly one smoke board;
4. verify the saved object contains flop, turn chance/action nodes, river chance/action nodes and strategy payloads;
5. only then generalize it to batch studies.

Do not launch a 286-board batch merely to discover the exporter. One board is enough for runner development.

## What must not return to `main`

Until the user explicitly starts a new research cycle, do not add:

- `datasets/`;
- `analysis/`;
- `results/`;
- `studies/`;
- old strategy reports/EXP artifacts;
- node-specific dataset collectors;
- guessed full-tree export probes.

Old files remain recoverable from Git history. They are not active evidence.

## Git and CI

The user authorizes direct commits/pushes to `main` for normal repository work.

Before replacing a file, fetch current remote `main`. After runner changes:

- run/update static CI;
- inspect the actual GitHub Actions job logs, not only the status badge;
- keep the baseline documentation synchronized with proven behavior.

GPU/runtime tests execute on the user's Windows/NVIDIA machine. Do not pretend GitHub-hosted CI can perform the real solver solve.

## Connected facts

TexasSolverGPU workflow here starts postflop. Preflop ranges/pot/stack are inputs; preflop is not solved.

The current baseline supports node-specific/current-street export only. The architectural requirement for future runner work is: **solve the configured tree once, persist the complete solved tree, analyze arbitrary nodes later without another GPU solve.**

## First files to read in a new chat

1. `AGENTS.md`
2. `README.md`
3. `docs/BASELINE.md`
4. `docs/BRIDGE_SCHEMA.md`
5. `docs/HISTORY.md`

Do not reconstruct current behavior from old conversation memory when `main` can be read.

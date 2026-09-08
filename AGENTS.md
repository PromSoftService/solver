# Mandatory instructions for PromSoftService/solver

Remote `main` is the source of truth. Read this file before changing the repository.

## Purpose

This repository automates the original `TexasSolverGpu_131.exe` from TexasSolverGPU v0.2.0 Windows x64. Do not replace or reimplement the solver.

The accepted production model is intentionally narrow: solve the configured postflop tree with the GPU engine, navigate to one configured decision history, and export that current-street node through the verified stock bridge.

## Proven baseline

- `tsgpu-worker.ps1` retains the proven `v015-production` startup/solve/export core from historical commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`.
- `tsgpu-batch.ps1` processes arbitrary board lists and can read solve/decision settings from the JSON `runner` block.
- `solver.history.apply`, `solver.node.actionsAfter`, and `solver.export.currentStreet` select and export one branch.
- The original WebView2 host and CUDA solver remain unchanged.

Complete solved-tree persistence is not a production feature. Do not describe a current-street export as a reloadable full-tree save.

## Repository policy

Keep source inputs and reusable examples in Git. Generated `output/` and `_diagnostics/` data stay ignored. Do not add calculated datasets, analyses, study results, or solver binaries unless the user explicitly requests them.

## Full-tree research history

The installed runtime exposes no monolithic full-tree save/load method. A diagnostic proved that the solved tree can be reconstructed by repeatedly combining `solver.history.apply`, `solver.cards.possible`, and `solver.export.currentStreet`. The complete one-board proof required 33,125 fragments, about 18.3 minutes of extraction, and a 589 MB archive. It was rejected as a production architecture.

Do not restore exhaustive traversal or guessed APIs (`fullTree`, `fullStrategy`, `dumpStrategy`, and similar names) without a new explicit user decision. The proof remains documented in `docs/HISTORY.md` and Git history.

## Git and validation

Before replacing files, fetch remote `main`. After runner changes:

- parse every PowerShell file;
- validate JSON examples and board syntax;
- run the smallest relevant smoke on the user's Windows/NVIDIA machine;
- inspect output files and batch summaries;
- inspect GitHub Actions logs after pushing.

GitHub-hosted CI cannot prove a CUDA solve. Never claim a runtime result that was not produced on the Windows/NVIDIA host.

## First files to read

1. `AGENTS.md`
2. `README.md`
3. `docs/BASELINE.md`
4. `docs/BRIDGE_SCHEMA.md`
5. `docs/HISTORY.md`

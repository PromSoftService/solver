# Mandatory instructions for working with PromSoftService/solver

Read this file before changing the repository. Remote `main` is the source of truth.

## 1. Purpose

The repo automates the original `TexasSolverGpu_131.exe` from TexasSolverGPU v0.2.0. Never replace/reimplement the solver unless the user explicitly asks.

The user wants headless/batch operation. Do not send the user into the GUI when the runner can do the work.

## 2. Core study architecture — do not regress

A registered study defines one complete **postflop game tree**. For each flop board:

1. initialize the native solver with fixed preflop ranges/pot/stack and all configured postflop actions;
2. solve the entire configured tree once;
3. export and preserve the complete solved tree, including flop, turn and river strategy/chance/action nodes;
4. validate that the export actually contains turn and river nodes;
5. only later derive analytical datasets from the saved tree.

Never rerun the GPU solver merely to export another decision node from an already solved tree.

Analytical reports never define the tree. A later report may inspect only BB defense vs B33 while the stored result still contains every branch that was actually configured in that study.

## 3. Active study — STU002

STU002 intentionally restores the **exact historical CFG001 action abstraction** because the larger multi-sizing STU001 tree is too slow for the user's workflow. The full-tree result contract remains mandatory.

Inputs: RNG001 + BRD001 (286 canonical unpaired rainbow flops), UTG open 2.5bb -> BB call, 5.5bb flop pot, 97.5bb effective stack.

Exact active tree:

- flop OOP open bet: none;
- flop IP open bet: 33%;
- flop OOP raise parameter: 60;
- flop IP raise parameter: 100;
- turn OOP/IP bet: 100%;
- turn OOP donk: 100%;
- turn OOP/IP raise: 100%;
- river OOP/IP bet: 100%;
- river OOP donk: 100%;
- river OOP/IP raise: 100%;
- `maxRaiseNumber = 3`;
- `addAllinThreshold = 200` in the study JSON, which the worker converts to native `2.0` exactly as in historical CFG001;
- all six add-all-in street/player flags are enabled exactly as in historical CFG001.

These values are copied from commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`, file `configs/CFG001__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B33_BB-XR60__T-B100-R100__R-B100-R100__V1.json`.

Do not reinterpret native raise parameters as fixed raise-to multiples. In particular `raise=60` is the TexasSolver native pot-raise parameter, not a universal exact `3x`.

STU001 remains registered as the larger multi-sizing full-tree experiment, but it is **not the active study** and should not be run unless the user explicitly asks.

## 4. Preflop scope

TexasSolverGPU in this workflow does not solve preflop. The study starts at the flop with already fixed OOP/IP ranges, pot and effective stack. Say “full postflop tree”, not “preflop to showdown”.

## 5. Full-tree export is mandatory

The proven v015 automation solved the configured tree correctly but exported only one selected decision node. That behavior is obsolete.

The current worker must preserve a complete solved postflop tree. A board is not accepted merely because the GPU solve finished. `tree.meta.json.full_tree_validated` must be true and the exported JSON must structurally contain turn and river strategy nodes.

If the installed runtime does not expose the full-tree bridge endpoint through the currently probed methods, fail immediately with `FULL_TREE_EXPORT_UNRESOLVED`, preserve `export-probes.json` and `bridge-transcript.jsonl`, and stop the batch. Do not silently fall back to node-only output and do not waste time solving the remaining boards.

## 6. Study completion and auto-push

A study launcher must:

- require a clean checkout whose HEAD matches `origin/main` before solving;
- isolate transient work under ignored `output/`;
- solve every requested board;
- validate every full-tree export;
- write reproducibility metadata and copy exact inputs;
- if any board/export fails: STOP, do not commit/push results;
- after total success: move the run to `results/`, `git add`, commit, rebase on current `origin/main`, push `main`.

The user should normally run one command only.

Active command:

```powershell
.\scripts\RUN__STU002__BRD001__AND_PUSH.cmd
```

Resume only after an exporter/runtime issue has been fixed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-STU002.ps1 -Resume
```

## 7. Results and analysis

`results/` stores versioned solved-tree study runs. `analysis/` starts empty after the 2026-09-08 reset. Analysis must read saved full trees; it must never require a new GPU solve just to inspect a different node/street.

When simplifying poker strategy later:

- weight by reach probability;
- distinguish local forced-action loss from adaptive exploitability;
- do not use equity unless explicitly requested;
- optimize for human-executable rules, not solver-frequency cloning;
- keep source solver profiles and any simplification artifacts reproducible.

## 8. Historical studies

The old CFG001/CFG002/CFG003 node-specific datasets and universal-strategy EXP-001..004 were removed from current `main`. Their methodology/history is summarized in `docs/HISTORY.md`, and their exact files remain recoverable from Git history (notably commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`).

Historical CFG001 **tree settings** are intentionally reused by active STU002; its old node-only result datasets are not active evidence.

## 9. Git rules

The user authorizes direct commits/pushes to `main` for normal repository work. Fetch current files before replacing them. Do not overwrite newer remote changes from memory.

For runner/study changes, update static CI and inspect actual job logs. GPU solves themselves run on the user's Windows/NVIDIA machine.

## 10. First files to read in a new chat

1. `AGENTS.md`
2. `README.md`
3. `docs/ARCHITECTURE.md`
4. `docs/STUDY_REGISTRY.md`
5. `docs/BRIDGE_SCHEMA.md`
6. latest relevant `results/STU002__.../RUN_MANIFEST.json` if one exists

Do not reconstruct current behavior from old chat memory when `main` can be read.

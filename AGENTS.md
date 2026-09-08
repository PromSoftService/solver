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

Never create separate solves for alternative bet sizes that should compete at the same node. Example: B33 and B75 must coexist in one tree if both are allowed in the strategy.

## 3. Active abstraction

For STU001:

- flop normal bets: 33%, 75%; plus all-in;
- turn normal bets: 33%, 75%; plus all-in;
- river normal bets: 33%, 75%, 150%; plus all-in;
- native normal raise: 60% pot-raise; plus all-in;
- max normal raise count per street: 1;
- OOP turn/river donks: same normal bet sizes;
- all-in enabled on every street.

Do not describe native `raise=60` as exactly `3x`. It is the TexasSolver pot-raise parameter and its resulting raise-to multiple depends on the preceding bet/pot.

## 4. Preflop scope

TexasSolverGPU in this workflow does not solve preflop. The study starts at the flop with already fixed OOP/IP ranges, pot and effective stack. Say “full postflop tree”, not “preflop to showdown”.

## 5. Study completion and auto-push

A study launcher must:

- require a clean checkout whose HEAD matches `origin/main` before solving;
- isolate transient work under ignored `output/`;
- solve every requested board;
- validate every full-tree export;
- write reproducibility metadata and copy exact inputs;
- if any board/export fails: STOP, do not commit/push results;
- after total success: move the run to `results/`, `git add`, commit, rebase on current `origin/main`, push `main`.

The user should normally run one command only.

## 6. Results and analysis

`results/` stores versioned solved-tree study runs. `analysis/` starts empty after the 2026-09-08 reset. Analysis must read saved full trees; it must never require a new GPU solve just to inspect a different node/street.

When simplifying poker strategy later:

- weight by reach probability;
- distinguish local forced-action loss from adaptive exploitability;
- do not use equity unless explicitly requested;
- optimize for human-executable rules, not solver-frequency cloning;
- keep source solver profiles and any simplification artifacts reproducible.

## 7. Historical studies

The old CFG001/CFG002/CFG003 datasets and universal-strategy EXP-001..004 were removed from current `main`. Their methodology/history is summarized in `docs/HISTORY.md`, and their exact files remain recoverable from Git history (notably commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`). Do not silently reuse those datasets as active evidence.

## 8. Git rules

The user authorizes direct commits/pushes to `main` for normal repository work. Fetch current files before replacing them. Do not overwrite newer remote changes from memory.

For runner changes, add/update static CI and inspect actual job logs. GPU solves themselves run on the user's Windows/NVIDIA machine.

## 9. First files to read in a new chat

1. `AGENTS.md`
2. `README.md`
3. `docs/ARCHITECTURE.md`
4. `docs/STUDY_REGISTRY.md`
5. latest relevant run manifest under `results/` if one exists

Do not reconstruct current behavior from old chat memory when `main` can be read.

# TexasSolverGPU full-tree study runner

This repository is the automation and study workspace around the original **TexasSolverGPU v0.2.0 Windows x64** binary. It does not implement a poker solver.

## Current principle

One board is solved **once** from the flop root through the complete configured postflop abstraction. The runner then preserves the complete solved strategy tree. Later analysis may inspect flop, turn, river and any response node without repeating the GPU solve.

A study is considered complete only when every requested board has:

- a successful native solve;
- a verified full-tree export containing flop, turn and river strategy nodes;
- run metadata and input hashes;
- no missing board result.

Only after the whole study passes validation does its launcher move the run into `results/`, create a Git commit, and push `main`. A partial or failed study is never committed automatically.

## Active study: STU002

`STU002` keeps the new **full-tree export architecture** but deliberately returns to the old compact CFG001 poker tree because the larger multi-sizing STU001 tree is too slow for practical batch solving.

Inputs:

- 6-max NLHE cash, 100bb;
- UTG open 2.5bb -> BB call;
- TexasSolverGPU bundled UTG/BB weighted ranges (`RNG001`);
- `BRD001`: 286 canonical unpaired rainbow flops;
- flop pot 5.5bb, effective stack 97.5bb.

Exact tree settings copied from historical CFG001:

- flop BB/OOP open bet: none;
- flop UTG/IP bet: **33% only**;
- flop BB/OOP raise parameter: **60**;
- flop UTG/IP raise parameter: **100**;
- turn bets/donk/raises: **100**;
- river bets/donk/raises: **100**;
- `maxRaiseNumber = 3`;
- `addAllinThreshold = 200` (worker converts to native `2.0` exactly as before);
- add-all-in flags enabled for both players on flop/turn/river.

The only architectural change versus old CFG001 is the output: **save and validate the complete solved postflop tree, not one selected node.**

This is a postflop solve. Preflop is not solved: ranges, pot and effective stack are fixed inputs.

## Full-tree export

The proven v015 automation handles startup/init/allocate/solve/polling. The current worker keeps that proven solve path but replaces node-only export with a full-tree contract.

A board is accepted only if the exported JSON contains nested strategy/action/chance structure through both turn and river. If the installed runtime does not expose the required full-tree export through the probed bridge methods, the first board stops with:

```text
FULL_TREE_EXPORT_UNRESOLVED
```

The failed board preserves `export-probes.json` and `bridge-transcript.jsonl`. The batch stops immediately rather than wasting the remaining GPU solves. After exporter discovery is fixed, resume the same study.

## User command

After synchronizing the local checkout to remote `main`, run from the repository root:

```powershell
.\scripts\RUN__STU002__BRD001__AND_PUSH.cmd
```

The launcher verifies the checkout is clean/current, solves all 286 boards, validates all full-tree exports, then commits and pushes the completed result automatically.

Resume after an exporter/runtime fix:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-STU002.ps1 -Resume
```

## Registered but inactive

`STU001` is retained as the earlier larger multi-sizing full-tree study definition. It is not active because its action tree is too expensive for the current workflow. Do not run it unless explicitly requested.

See:

- `AGENTS.md` — mandatory operating rules;
- `docs/ARCHITECTURE.md` — solve/export architecture;
- `docs/STUDY_REGISTRY.md` — immutable study definitions;
- `docs/BRIDGE_SCHEMA.md` — bridge/export contract;
- `docs/HISTORY.md` — lessons from the discarded node-only research cycle.

# TexasSolverGPU full-tree study runner

This repository is the automation and study workspace around the original **TexasSolverGPU v0.2.0 Windows x64** binary. It does not implement a poker solver.

## Current principle

One board is solved **once** from the flop root through the complete configured postflop abstraction. The runner then preserves the complete solved strategy tree. Later analysis may inspect flop, turn, river, any bet-size branch, and any response node without repeating the GPU solve.

A study is considered complete only when every requested board has:

- a successful native solve;
- a verified full-tree export containing flop, turn and river strategy nodes;
- run metadata and input hashes;
- no missing board result.

Only after the whole study passes validation does its launcher move the run into `results/`, create a Git commit, and push `main`. A partial or failed study is never committed automatically.

## Active study

`STU001` is the new clean baseline:

- 6-max NLHE cash, 100bb;
- UTG open 2.5bb -> BB call;
- TexasSolverGPU bundled UTG/BB weighted ranges (`RNG001`);
- `BRD001`: 286 canonical unpaired rainbow flops;
- both players may use B33/B75 on flop and turn;
- both players may use B33/B75/B150 on river;
- native normal raise size = 60% pot-raise plus all-in;
- at most one normal raise per street in the abstraction; all-in remains available;
- all-in is enabled on every street;
- OOP donk branches on turn/river use the same normal bet sizes.

This is a **postflop** solve. Preflop is not solved: ranges, 5.5bb flop pot and 97.5bb effective stack are fixed inputs.

## User command

After synchronizing the local checkout to remote `main`, run from the repository root:

```powershell
.\scripts\RUN__STU001__BRD001__AND_PUSH.cmd
```

The launcher verifies the checkout is clean/current, solves all 286 boards, validates all exports, and then commits/pushes the completed result automatically.

## Important

Do not create separate solves for B33 and B75. Both sizes must coexist in the **same tree** so branch ranges are endogenous to the same equilibrium solve.

See:

- `AGENTS.md` — mandatory handoff instructions for ChatGPT;
- `docs/ARCHITECTURE.md` — runner/export architecture;
- `docs/STUDY_REGISTRY.md` — immutable study/input definitions;
- `docs/HISTORY.md` — what was learned from the discarded first research cycle.

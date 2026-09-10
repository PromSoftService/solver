# STU002 — complete UTG vs BB flop interaction

This study covers all six normal-action decision points on the flop for RNG001
over all 286 BRD001 boards. Every branch remains an independent stock runner
job: one board, one GPU solve, one configured history and one
`solver.export.currentStreet` call.

## Abstraction

- Flop: BB bet/donk 50%, UTG bet 50%, raise 60 native.
- Turn: OOP bet/donk 50%, IP bet 50%, raise 60 native.
- River: OOP bet/donk 75%, IP bet 100%, raise 60 native.
- One normal raise after the opening bet (`maxRaiseNumber=2` natively).
- Proven v015 all-in flags and `addAllinThreshold=200` are unchanged.

Turn and river are continuation abstractions required for valid flop EVs. This
study exports and analyzes only flop decisions.

## Six independent branches

| ID | Exported decision |
|---|---|
| `01_BB_FIRST` | BB at flop root: check or donk |
| `02_UTG_AFTER_CHECK` | UTG after BB checks |
| `03_BB_AFTER_CBET` | BB after check and UTG bet |
| `04_UTG_AFTER_CHECK_RAISE` | UTG after BB check-raises |
| `05_UTG_AFTER_DONK` | UTG after BB donks |
| `06_BB_AFTER_DONK_RAISE` | BB after UTG raises the donk |

## Run one branch

From the repository root:

```powershell
.\studies\STU002__RNG001_UTG-vs-BB__BRD001_FLOP6\run-branch.ps1 -BranchId 01_BB_FIRST
```

Use `-Resume` only with the unchanged config and the same output directory.
The default raw output is `output/STU002.../<branch>/`; compact reports and an
aggregate analysis-ready `combos.csv` are written under
`datasets/STU002.../<branch>/<UTC timestamp>/` after 286/286 succeeds.

## Run all branches sequentially

```powershell
.\studies\STU002__RNG001_UTG-vs-BB__BRD001_FLOP6\run-all.ps1
```

This performs 1716 independent GPU solves and is expected to take roughly
11–12 hours on the measured Windows/NVIDIA host. It does not use multi-export,
full-tree traversal, guessed APIs or custom tree persistence.

## Build the human strategy after all six datasets exist

The completed compact datasets are already tracked. Rebuilding the strategy
does not run the solver again:

```text
python scripts/generate-flop-strategies.py STU002__RNG001_UTG-vs-BB__BRD001_FLOP6
node scripts/build-flop-workbooks.mjs STU002__RNG001_UTG-vs-BB__BRD001_FLOP6
```

The first command produces both the B13 and eight-flop-category policies from
raw combo frequencies. The second produces the two approved Excel workbooks.
See `docs/FLOP_STRATEGY_WORKFLOW.md` for the complete frozen algorithm.

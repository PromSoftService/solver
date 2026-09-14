# STU005 — complete BTN vs BB flop interaction

This study covers all six normal-action decision points on the flop for RNG003
over all 286 BRD001 boards. BTN opened 2.5 bb, BB called, and BTN is in
position postflop. Every branch is an independent stock runner job: one board,
one GPU solve, one configured history and one current-street export.

## Abstraction

- Flop: BB bet/donk 50%, BTN bet 50%, raise 60 native.
- Turn: OOP bet/donk 50%, IP bet 50%, raise 60 native.
- River: OOP bet/donk 75%, IP bet 100%, raise 60 native.
- One normal raise after the opening bet (`maxRaiseNumber=2` natively).
- Proven v015 all-in flags and `addAllinThreshold=200` remain unchanged.

Turn and river are continuation abstractions required for valid flop EVs.
STU005 exports and analyzes only flop decisions.

## Six independent branches

| ID | Exported decision |
|---|---|
| `01_BB_FIRST` | BB at flop root: check or donk |
| `02_BTN_AFTER_CHECK` | BTN after BB checks |
| `03_BB_AFTER_CBET` | BB after check and BTN c-bet |
| `04_BTN_AFTER_CHECK_RAISE` | BTN after BB check-raises |
| `05_BTN_AFTER_DONK` | BTN after BB donks |
| `06_BB_AFTER_DONK_RAISE` | BB after BTN raises the donk |

## Prepare and validate config without solving

From the repository root:

```powershell
node .\scripts\generate-study-config.mjs STU005
```

## Run one branch later

```powershell
.\studies\STU005__RNG003_BTN-vs-BB__BRD001_FLOP6\run-branch.ps1 -BranchId 01_BB_FIRST
```

Use `-Resume` only with the unchanged config and output directory.

## Run all branches later

```powershell
.\studies\STU005__RNG003_BTN-vs-BB__BRD001_FLOP6\run-all.ps1
```

This means 1716 independent GPU solves. No GPU solve is part of study
preparation. Raw output remains under ignored `output/`; compact successful
reports are written under `datasets/`.

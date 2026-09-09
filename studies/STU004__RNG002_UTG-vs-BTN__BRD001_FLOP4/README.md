# STU004 — RNG002 UTG vs BTN BRD001 flop study

This is the production expansion of the proven STU003 five-flop pilot. It runs
the same four selected flop decisions over all 286 canonical unpaired rainbow
BRD001 flops: 1,144 independent stock solves and current-street exports.

## Spot and abstraction

- OOP: UTG; IP: BTN.
- Flop pot: 6.5 bb (`startingPot=65`).
- Effective flop stack: 97.5 bb (`effectiveStack=975`).
- Ranges: exact RNG002 weighted combo arrays from the TexasSolverGPU v0.2.0
  bundled 6-max range library.
- Flop and turn normal bets: 50% pot.
- River: OOP 75%, IP 100%.
- Native raise size: 60; one normal raise after the opening bet
  (`maxRaiseNumber=2`).
- Proven v015 all-in flags and `addAllinThreshold=200` remain unchanged.

The two decisions after a flop raise remain outside this iteration. Turn and
river are solved only as continuation abstractions and are not exported or
analyzed.

## Run

From the repository root:

```powershell
.\studies\STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4\run-all.ps1
```

The four branches run sequentially. Raw node output remains under ignored
`output/`; compact validated reports are written below `datasets/STU004.../`.
Use `-Resume` only with unchanged config and the same output root. The runner
reuses complete boards and retries only missing or failed ones.

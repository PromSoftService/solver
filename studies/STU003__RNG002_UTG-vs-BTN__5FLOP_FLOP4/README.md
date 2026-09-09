# STU003 — RNG002 UTG vs BTN five-flop pilot

This pilot runs four selected flop decisions for UTG open 2.5 bb / BTN call.
Each branch uses five canonical BRD001 flops. The two decisions after a flop
raise are deliberately excluded from the current scope.

## Spot and abstraction

- OOP: UTG; IP: BTN.
- Flop pot: 6.5 bb (`startingPot=65`).
- Effective flop stack: 97.5 bb (`effectiveStack=975`).
- Ranges: exact RNG002 weighted combo arrays.
- Flop and turn normal bets: 50% pot.
- River: OOP 75%, IP 100%.
- Native raise size: 60; one normal raise after the opening bet
  (`maxRaiseNumber=2`).
- Existing v015 all-in flags and `addAllinThreshold=200` are unchanged.

The expected native flop amounts are bet 33 and raise-to 112. The runner checks
these values on the relevant branches.

## Four branches

| ID | Exported decision |
|---|---|
| `01_UTG_FIRST` | UTG at the flop root: check or bet |
| `02_BTN_AFTER_CHECK` | BTN after UTG checks: check or bet |
| `03_BTN_AFTER_CBET` | BTN after UTG bets: fold, call or raise |
| `04_UTG_AFTER_STAB` | UTG after checking and facing a BTN bet: fold, call or raise |

Every board/branch performs one GPU solve and one stock
`solver.export.currentStreet`. Total pilot scope is 20 independent solves.

## Run

From the repository root:

```powershell
.\studies\STU003__RNG002_UTG-vs-BTN__5FLOP_FLOP4\run-all.ps1
```

`run-all.ps1` measures one wall-clock interval from script launch through the
last branch's validation, combo parsing and compact report generation. It
writes `operation-timing.json` and prints cumulative elapsed time before and
after every branch. Each branch also records solver-batch time separately from
validation/parsing time.

Raw output stays under ignored `output/`. Compact pilot evidence is written
under `datasets/STU003__RNG002_UTG-vs-BTN__5FLOP_FLOP4/<UTC timestamp>/`.

Use `-Resume` only without changing the config, board list or output root.

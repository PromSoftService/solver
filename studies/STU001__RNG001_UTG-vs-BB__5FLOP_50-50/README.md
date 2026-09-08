# STU001 — RNG001 UTG vs BB, five-flop 50/50 test

This is the first production performance study after restoring the stock
`v015-production` current-street workflow.

## Spot

- UTG opens 2.5bb, BB calls.
- OOP: BB; IP: UTG.
- Flop pot: 5.5bb (`startingPot=55`).
- Effective flop stack: 97.5bb (`effectiveStack=975`).
- Ranges: RNG001 exact weighted combo arrays.

## Tree abstraction

- Flop: OOP bet/donk 50%, IP bet 50%, raise 60 native.
- Turn: OOP bet/donk 50%, IP bet 50%, raise 60 native.
- River: OOP bet/donk 75%, IP bet 100%, raise 60 native.
- Maximum one normal raise after the opening bet per street. TexasSolver's
  native counter includes the opening bet, so this is encoded as
  `maxRaiseNumber=2`.
- All-in flags and threshold retain the existing proven v015 semantics.

The exported decision is `BB_RESPONSE`: BB checks, UTG bets 50%, BB acts.
With the x10 money scale, the expected native bet is 28 and the expected
raise-to amount is 95. These are checked by the runner.

## Boards

The five flops are canonical BRD001 representatives from different B13-v2
regions: `A[K/Q]x`, `BBx high`, `BBx low`, `[J-8]x partial`, and `[7-4]x`.

## Run

From the repository root:

```powershell
.\studies\STU001__RNG001_UTG-vs-BB__5FLOP_50-50\run.ps1
```

Raw node output stays under ignored `output/`. The launcher writes compact,
trackable timing and validation reports under `datasets/`.

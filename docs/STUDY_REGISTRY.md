# Study registry — clean generation

Study/input IDs are immutable. If ranges, board family, stack/pot, tree actions, or output contract change, create a new ID/version.

## RNG001

6-max NLHE cash, 100bb. Preflop branch is fixed externally:

`UTG open 2.5bb -> BB call`

Source: TexasSolverGPU v0.2.0 bundled 6-max range library, path `ranges/6max_range/UTG/2.5bb/BB/Call`.

- flop pot: 5.5bb;
- effective stack on flop: 97.5bb;
- OOP: BB;
- IP: UTG.

Do not label these ranges as GTO Wizard ranges; public upstream provenance is not documented.

## BRD001

286 canonical unpaired rainbow flops, one representative for every three-distinct-rank combination: `C(13,3)=286`.

## STU001 — larger multi-sizing full-tree baseline (inactive)

Inputs: `RNG001 + BRD001`.

Tree:

| Street | Open bet sizes | OOP donk | Normal raise | All-in |
|---|---|---|---|---|
| Flop | 33%, 75% | n/a | native 60% pot-raise | enabled |
| Turn | 33%, 75% | 33%, 75% | native 60% pot-raise | enabled |
| River | 33%, 75%, 150% | 33%, 75%, 150% | native 60% pot-raise | enabled |

`maxRaiseNumber = 1`; all-in threshold was intentionally raised to expose all-in from the flop.

Status: **registered but inactive**. The tree is too slow for the current 286-board workflow. Do not run unless explicitly requested.

## STU002 — UTG vs BB legacy CFG001 sizing + full-tree export (ACTIVE)

Inputs: `RNG001 + BRD001`.

STU002 reuses the exact tree-action settings from historical CFG001, commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`, but changes the result contract from node-specific export to **complete postflop tree export**.

Exact native-config source values:

| Setting | Value |
|---|---:|
| `oopFlopBet` | empty |
| `ipFlopBet` | `33` |
| `oopFlopRaise` | `60` |
| `ipFlopRaise` | `100` |
| `oopTurnBet` / `ipTurnBet` | `100` |
| `oopTurnDonk` | `100` |
| `oopTurnRaise` / `ipTurnRaise` | `100` |
| `oopRiverBet` / `ipRiverBet` | `100` |
| `oopRiverDonk` | `100` |
| `oopRiverRaise` / `ipRiverRaise` | `100` |
| `maxRaiseNumber` | `3` |
| `addAllinThreshold` | `200` study value -> native `2.0` after worker conversion |
| all six add-all-in flags | `true` |

Solve defaults:

- max iterations: 1000;
- target exploitability: 0.5;
- compression disabled for export fidelity.

Output contract: one complete validated strategy tree through river for every BRD001 flop. No node-specific dataset is generated during the GPU study.

Primary launcher:

```powershell
.\scripts\RUN__STU002__BRD001__AND_PUSH.cmd
```

Successful 286/286 completion automatically creates a result commit and pushes `main`. Any solve/export failure leaves only ignored transient output and performs no result push.

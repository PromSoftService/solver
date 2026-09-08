# Study registry — clean generation

Study/input IDs are immutable. If ranges, board family, stack/pot, or tree actions change, create a new ID/version.

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

## STU001 — UTG vs BB full postflop baseline

Inputs: `RNG001 + BRD001`.

Tree actions for both players:

| Street | Open bet sizes | OOP donk | Normal raise | All-in |
|---|---|---|---|---|
| Flop | 33%, 75% | n/a (OOP root betting uses open-bet sizes) | native 60% pot-raise | enabled |
| Turn | 33%, 75% | 33%, 75% | native 60% pot-raise | enabled |
| River | 33%, 75%, 150% | 33%, 75%, 150% | native 60% pot-raise | enabled |

`maxRaiseNumber = 1` for normal raises. All-in remains a separate available action.

The all-in-add threshold is configured high enough to allow all-in from the flop at the initial ~17.7 SPR.

Solve defaults:

- max iterations: 1000;
- target exploitability: 0.5 (solver's configured unit/semantics);
- compression disabled for export fidelity.

Output contract: a complete strategy tree through river for every board. No node-specific dataset is generated during the GPU study.

Primary launcher:

```powershell
.\scripts\RUN__STU001__BRD001__AND_PUSH.cmd
```

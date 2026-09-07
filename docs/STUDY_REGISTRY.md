# Study registry

Study IDs are immutable. If the underlying ranges, tree, board definition, or decision-node semantics change, create a new ID or a new `Vn` file; do not silently reuse an existing ID.

## Ranges

| ID | Definition | Source |
|---|---|---|
| `RNG001` | 6-max NLHE cash, 100bb, UTG open 2.5bb, BB call | TexasSolverGPU v0.2.0 bundled 6-max range library |
| `RNG002` | 6-max NLHE cash, 100bb, UTG open 2.5bb, BTN call | TexasSolverGPU v0.2.0 bundled 6-max range library |

`RNG001` is the permanent baseline for the first study family. The public TexasSolverGPU repository does not document an upstream provider for these ranges, so they are deliberately **not** labeled as GTO Wizard ranges.

`RNG002` uses the matched weighted UTG-open and BTN-call files from `ranges/6max_range/UTG/2.5bb/BTN/Call` in the bundled TexasSolverGPU library. The UTG range is numerically identical to the UTG range already used by `RNG001`; the BTN range is the bundled BTN call branch. Keep the original fractional weights. `RNG002` has 233.916 weighted UTG combos and 113.604 weighted BTN combos.

Files:

- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1.json`
- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__UTG.txt`
- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__BB.txt`
- `ranges/RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1.json`
- `ranges/RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1__UTG.txt`
- `ranges/RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1__BTN.txt`

## Configs

| ID | Solver tree | Native money scale |
|---|---|---:|
| `CFG001` | UTG open 2.5bb, BB call; flop BB check, UTG Check or Bet 33%; after Bet BB Fold/Call/XR60 | x10 |
| `CFG002` | Same spot/tree as CFG001, but UTG flop bet is 75% | x10 |
| `CFG003` | UTG open 2.5bb, BTN call; flop UTG Check or Bet 33%; after Check BTN Check or Bet 33%; OOP raise 60%, IP raise 100% | x10 |

`CFG001` uses a flop pot of 55 and effective stack of 975, representing 5.5bb and 97.5bb at x10 scale. Its native flop bet is `Bet 18`; after that bet the configured BB raise is `Raise 73`.

`CFG002` is intentionally derived from `CFG001`: the only tree change is `ipFlopBet = 75` instead of `33`. Its native flop bet is `Bet 41` and the configured BB raise is `Raise 123`. BB flop raise remains `60`, and all turn/river sizings, ranges, stack, pot, rake and solver settings remain unchanged. To avoid duplicating the two 1326-entry range arrays in Git, the persistent definition is stored as:

- `configs/CFG002__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B75_BB-XR60__T-B100-R100__R-B100-R100__V1.derived.json`

The CFG002 launcher materializes the full effective native config in a temporary file, validates the expected native actions, and `Run-Study.ps1` copies that effective config into the raw run directory before the temporary file is removed.

`CFG003` is the first UTG-versus-BTN tree. UTG is OOP. The flop pot is 65 and effective stack is 975, representing 6.5bb and 97.5bb. At the root UTG has `Check / Bet 33%`; the expected native wager is 21. If UTG checks, BTN has `Check / Bet 33%`. Flop raise settings are OOP 60% and IP 100%; turn and river bet/raise settings remain 100%/100% as inherited from CFG001. The persistent definition is:

- `configs/CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.derived.json`

The CFG003 launcher expands the TexasSolver shorthand range files to the exact native 1326-combo order, materializes the full config, and validates the UTG root wager before exporting the requested node.

## Decision nodes

Decision-node IDs identify **which solved node is exported**. They do not change the underlying solver tree.

| ID | Runner value | Acting player | Exported node/actions |
|---|---|---|---|
| `NOD001` | `BB_RESPONSE` | BB | after `BB Check -> UTG configured Bet`; `Fold / Call / Raise` |
| `NOD002` | `UTG_CBET` | UTG | after `BB Check`, before any UTG action; `Check / configured Bet` |
| `NOD003` | `UTG_OOP_CBET` | UTG | flop root in UTG-vs-BTN SRP, before any flop action; `Check / configured OOP Bet` |

`NOD001` is the semantics used by the original CFG001/CFG002 datasets. Older launchers keep their historical output names and therefore omit the node ID, but they still run with the default `BB_RESPONSE` extraction.

`NOD002` is the UTG IP flop c-bet study for `CFG001`. The tree and ranges are unchanged: after BB checks, UTG has only `Check` and `Bet 33%` at the target node. With the x10 native money scale the runner validates `Bet 18`, then exports the UTG strategy before applying that bet.

`NOD003` exports UTG's OOP decision at the **flop root** for `CFG003`, before UTG takes any action. The semantic actions are `Check / Bet 33%`; the launcher validates the native wager amount 21. The exported dataset uses the same UTG check/bet field schema as `NOD002`.

Launchers:

```powershell
.\scripts\RUN__CFG001__BRD001.cmd
.\scripts\RUN__CFG002__BRD001.cmd
.\scripts\RUN__CFG001__NOD002__BRD001.cmd
.\scripts\RUN__CFG003__NOD003__BRD001.cmd
```

## Board sets

| ID | Definition | Boards |
|---|---|---:|
| `BRD001` | Unpaired rainbow flops, one canonical suit-isomorphic representative for every three-distinct-rank combination | 286 |

`BRD001` runs from `As Kh Qd` through `4s 3h 2d`. There are `C(13,3) = 286` distinct rank triples. With suit-symmetric preflop ranges, each representative stands for the corresponding rainbow suit-isomorphism class.

## Output naming

Historical/default BB-response runs keep the original names:

```text
output/OUT__RNG001__<CFGID>__BRD001__RUN-YYYYMMDD-HHMMSS/
datasets/DS__RNG001__<CFGID>__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Runs with an explicit decision ID include it in the name. Examples:

```text
output/OUT__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS/
datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS.csv

output/OUT__RNG002__CFG003__NOD003__BRD001__RUN-YYYYMMDD-HHMMSS/
datasets/DS__RNG002__CFG003__NOD003__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Every run stores a `RUN_MANIFEST.json` with IDs, decision-node semantics, OOP/IP positions, input filenames, SHA-256 hashes, money scale, expected action amounts, and board count. A copy of the manifest is stored next to the analysis dataset.

## Dataset schemas

`NOD001 / BB_RESPONSE` keeps the existing BB schema: fold/call/raise frequencies, BB EVs, mixed EV, best/highest-frequency action, and EV loss from forcing each pure action.

`NOD002 / UTG_CBET` and `NOD003 / UTG_OOP_CBET` use the UTG schema:

- `board`, `combo`, `reach_probability`;
- `check_frequency`, `bet_frequency`;
- `ev_check_utg`, `ev_bet_utg`, `mixed_ev_utg` in bb;
- `best_ev_action` (`X` or `B`) and `best_ev_utg`;
- `highest_frequency_action`, `highest_frequency`;
- `loss_if_check_utg`, `loss_if_bet_utg`;
- iteration and final exploitability.

## Planned board families

Reserve new IDs rather than changing `BRD001`. Likely next families are unpaired two-tone, unpaired monotone, paired rainbow, paired two-tone, and then broader/all-flop sets.

# Study registry

Study IDs are immutable. If the underlying ranges, tree, board definition, or semantics change, create a new ID or a new `Vn` file; do not silently reuse an existing ID.

## Ranges

| ID | Definition | Source |
|---|---|---|
| `RNG001` | 6-max NLHE cash, 100bb, UTG open 2.5bb, BB call | TexasSolverGPU v0.2.0 bundled 6-max range library |

`RNG001` is the permanent baseline for the first study family. The public TexasSolverGPU repository does not document an upstream provider for these ranges, so they are deliberately **not** labeled as GTO Wizard ranges.

Files:

- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1.json`
- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__UTG.txt`
- `ranges/RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__BB.txt`

## Configs

| ID | Spot | Native money scale | Target node |
|---|---|---:|---|
| `CFG001` | UTG open 2.5bb, BB call; flop BB check, UTG bet 33%, BB response | x10 | `Check -> Bet 18 -> Fold/Call/Raise 73` |

`CFG001` uses a flop pot of 55 and effective stack of 975, representing 5.5bb and 97.5bb at x10 scale. The runner verifies the expected flop bet and raise amounts so a changed tree cannot silently produce the wrong dataset.

## Board sets

| ID | Definition | Boards |
|---|---|---:|
| `BRD001` | Unpaired rainbow flops, one canonical suit-isomorphic representative for every three-distinct-rank combination | 286 |

`BRD001` runs from `As Kh Qd` through `4s 3h 2d`. There are `C(13,3) = 286` distinct rank triples. With suit-symmetric preflop ranges, each representative stands for the corresponding rainbow suit-isomorphism class.

## Output naming

Raw runs:

```text
output/OUT__RNG001__CFG001__BRD001__RUN-YYYYMMDD-HHMMSS/
```

Analysis datasets:

```text
datasets/DS__RNG001__CFG001__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Every run stores a `RUN_MANIFEST.json` with IDs, input filenames, SHA-256 hashes, money scale, expected action amounts, and board count. A copy of the manifest is stored next to the analysis dataset.

## Planned board families

Reserve new IDs rather than changing `BRD001`. Likely next families are unpaired two-tone, unpaired monotone, paired rainbow, paired two-tone, and then broader/all-flop sets.

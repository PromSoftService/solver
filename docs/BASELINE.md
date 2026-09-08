# Production baseline

## Core lineage

The active worker is the proven `v015-production` solve/current-street implementation from historical commit:

`bec0b758fe7957a45d028f1adaa2a5252ff0598a`

The runner controls the original TexasSolverGPU v0.2.0 WebView2 host and CUDA engine. It does not implement poker solving itself.

## Supported workflow

For every board the runner performs:

1. `solver.init` with ranges, board, stack, pot and sizings;
2. `solver.allocate`;
3. one `solver.solve.start` and status polling;
4. stock history/action navigation to a configured decision;
5. one `solver.export.currentStreet`;
6. JSON/CSV output for that decision node.

The selected branch can be supplied through `runner.decisionNode` in the JSON config or overridden by `-DecisionNode`. Expected bet/raise amounts can also live in the config and prevent an accidental action mismatch.

## Explicit limitation

The output is a selected current-street node/subtree. It is not a complete solved tree and cannot be used to inspect arbitrary turn/river branches offline. Another branch requires another runner job and therefore another solve.

A full reconstruction was technically proven through repeated stock current-street exports, but its 33,125 round trips, ~18.3-minute extraction time and 589 MB archive made it unsuitable for production. That diagnostic code is not part of the runner.

## Fixtures

- `smoke/CFG001-one-board.json` plus `smoke/boards.txt`: one-board regression fixture.
- `example/config.json` plus `example/boards.txt`: documented five-board, one-flop-sizing example.
- `studies/STU001__RNG001_UTG-vs-BB__5FLOP_50-50/`: explicitly approved five-board performance study and report launcher.
- `studies/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/`: six independent selected-branch jobs covering the normal-action flop interaction over BRD001.
- `ranges/`: RNG001 and RNG002 source ranges.
- `boards/BRD001...txt`: 286 canonical source flops; never use it for routine runner smoke tests.

## Output contract

Each board directory contains:

- `run.json`: solver/config/decision metadata and final status;
- `node.raw.json`: native current-street payload;
- `combos.json` and `combos.csv`: normalized combo frequencies, reach probabilities and EVs;
- `bridge-transcript.jsonl`: exact methods, paths, bodies, timings and outcomes.

The batch root contains `batch-summary.json` and `batch-summary.csv`. Raw runtime output belongs under ignored `output/` or `_diagnostics/` directories. Explicitly approved compact study reports may be committed under `datasets/`.

## Operational risks

- Native schema compatibility is tied to TexasSolverGPU v0.2.0.
- `-Resume` assumes the config itself has not changed; use a fresh output directory when changing ranges/tree/solve settings.
- If the host exits before export, the solved in-memory state cannot be restored.
- The STU002 branch presets add only verified history navigation before the one
  stock current-street export; they do not change the solve/export boundary.

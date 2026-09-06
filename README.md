# TexasSolverGPU production batch runner v013

This repository automates the original TexasSolverGPU v0.2.0 native GPU/CUDA engine through its WebView2 bridge. It does not implement or substitute a poker solver.

## Directory layout

Keep this repository next to the untouched TexasSolverGPU installation:

```text
...\sotf\
  TexasSolverGpu-v0.2.0-windows-x64\
  tsgpu-batch-production-v013\
    boards\
    configs\
    ranges\
    scripts\
    tools\
    output\
    datasets\
    docs\
    examples\
    tsgpu-batch.cmd
    tsgpu-batch.ps1
    tsgpu-worker.ps1
```

The runner automatically searches for:

```text
..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe
```

You can also pass `-SolverExe` to `tsgpu-batch.ps1` or set `TSGPU_SOLVER_EXE`.

## Registered study runs

The permanent baseline is:

- `RNG001`: 6-max, 100bb, UTG open 2.5bb, BB call baseline ranges from the TexasSolverGPU v0.2.0 bundled range library;
- `BRD001`: 286 canonical unpaired rainbow flops, one for every three-distinct-rank combination.

Two flop trees are registered:

- `CFG001`: BB check -> UTG Check or Bet 33%; after Bet BB Fold/Call/XR60;
- `CFG002`: identical spot/tree, but UTG flop bet is 75%.

Decision-node extraction is separate from the tree:

- `NOD001 / BB_RESPONSE`: export the BB Fold/Call/Raise decision after the configured UTG bet;
- `NOD002 / UTG_CBET`: export the UTG Check/Bet decision immediately after BB checks.

Run from the repository root:

```powershell
.\scripts\RUN__CFG001__BRD001.cmd
.\scripts\RUN__CFG002__BRD001.cmd
.\scripts\RUN__CFG001__NOD002__BRD001.cmd
```

The first two commands preserve the existing BB-response studies. The third command is the new UTG flop c-bet study with the **same RNG001 ranges and CFG001 tree**: BB checks, then UTG has only `Check` or `Bet 33%` (`Bet 18` at the native x10 money scale).

`CFG001` validates native actions `Bet 18` and `Raise 73` for the legacy BB-response node.

`CFG002` is derived from CFG001 at runtime, changing only `ipFlopBet` from `33` to `75`. It validates native actions `Bet 41` and `Raise 123`. The full effective CFG002 native config is copied into the raw run directory, so the result remains reproducible without duplicating the two 1326-entry range arrays in Git.

All wrappers call the production GPU batch runner, build a single analysis CSV, copy all input definitions into the run directory, and write a manifest with SHA-256 hashes.

See `docs/STUDY_REGISTRY.md` for permanent ID and naming rules.

## Output

Historical/default BB-response runs keep the original naming:

```text
output\OUT__RNG001__<CFGID>__BRD001__RUN-YYYYMMDD-HHMMSS\
datasets\DS__RNG001__<CFGID>__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Runs with an explicit decision ID include it in the name. The UTG c-bet study writes:

```text
output\OUT__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS\
datasets\DS__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Each raw study directory contains:

```text
0001_<board>\
0002_<board>\
...
batch-summary.json
batch-summary.csv
dataset.csv
INPUT_CONFIG.json
INPUT_BOARDS.txt
INPUT_RANGE_PROFILE.json
INPUT_RANGE_UTG.txt
INPUT_RANGE_BB.txt
RUNNER_VERSION.txt
RUN_MANIFEST.json
```

Every board directory contains:

- `combos.json` and `combos.csv`: combo, reach probability, strategy frequencies, action EVs, and mixed EV for the selected decision node;
- `run.json`: board, convergence status, decision node, acting player, selected history/actions, and timing;
- `node.raw.json`: unmodified native current-street export at the selected node;
- `bridge-transcript.jsonl`: compact IPC audit trail.

Raw `output/` contents are ignored by Git. Analysis datasets under `datasets/` are intentionally versioned so completed studies can be pushed and reviewed later.

## Dataset fields

### BB response (`BB_RESPONSE`)

The existing schema is unchanged:

- board and combo;
- reach probability;
- fold/call/raise frequencies;
- EV of fold/call/raise in bb;
- mixed-strategy EV in bb;
- highest-frequency action;
- best-EV action;
- EV loss from forcing each pure action;
- iteration and final exploitability.

### UTG c-bet (`UTG_CBET`)

The new UTG schema contains:

- board and combo;
- reach probability;
- check and bet frequencies;
- `ev_check_utg`, `ev_bet_utg`, `mixed_ev_utg` in bb;
- best-EV action (`X`/`B`) and EV;
- highest-frequency action and frequency;
- `loss_if_check_utg`, `loss_if_bet_utg`;
- iteration and final exploitability.

## Low-level runner

For ad-hoc jobs you can still call the runner directly:

```powershell
.\tsgpu-batch.cmd .\examples\config.json .\examples\boards.txt .\output\test
```

or:

```powershell
.\tsgpu-batch.ps1 .\examples\config.json .\examples\boards.txt .\output\test
```

The default decision node remains `BB_RESPONSE`, so existing calls keep their old behavior.

To export the UTG c-bet node directly:

```powershell
.\tsgpu-batch.ps1 .\configs\CFG001__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B33_BB-XR60__T-B100-R100__R-B100-R100__V1.json `
  .\boards\BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt `
  .\output\utg-cbet-test `
  -DecisionNode UTG_CBET -ExpectedBetAmount 18
```

There is no artificial board-count limit. Blank lines and lines beginning with `#` in a board file are ignored.

Optional runner settings in a config are:

```json
"runner": {
  "maxIterations": 1000,
  "targetExploitability": 0.5
}
```

When omitted, those same defaults are used.

## Limitations

- Windows and Microsoft Edge WebView2 Runtime are required.
- The original TexasSolverGPU v0.2.0 installation and a compatible NVIDIA/CUDA setup are required.
- `UTG_CBET` expects exactly two actions at the target node: Check and the configured IP flop bet. The launcher validates `Bet 18` for CFG001.
- `BB_RESPONSE` targets the single-raise BB decision after BB check and the configured IP flop bet. Multiple IP bet sizes are ambiguous unless `-ExpectedBetAmount` is supplied.
- One native process per board is intentionally used for isolation. A crash on one board does not prevent later boards from running.
- `RNG001` is sourced from the bundled TexasSolverGPU range library. Its public upstream provenance is not documented, so it must not be described as a GTO Wizard range without separate evidence.

# TexasSolverGPU production batch runner v012

This repository automates the original TexasSolverGPU v0.2.0 native GPU/CUDA engine through its WebView2 bridge. It does not implement or substitute a poker solver.

## Directory layout

Keep this repository next to the untouched TexasSolverGPU installation:

```text
...\sotf\
  TexasSolverGpu-v0.2.0-windows-x64\
  tsgpu-batch-production-v012\
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

## Canonical study run

The first permanent study is already registered as:

- `RNG001`: 6-max, 100bb, UTG open 2.5bb, BB call baseline ranges from the TexasSolverGPU v0.2.0 bundled range library;
- `CFG001`: flop BB check -> UTG bet 33% -> BB Fold/Call/XR, with x10 native money scale;
- `BRD001`: 286 canonical unpaired rainbow flops, one for every three-distinct-rank combination.

Run it from the repository root:

```powershell
.\scripts\RUN__CFG001__BRD001.cmd
```

The wrapper calls the production GPU batch runner, validates the expected native flop actions (`Bet 18`, `Raise 73`), builds a single analysis CSV, copies all input definitions into the run directory, and writes a manifest with SHA-256 hashes.

See `docs/STUDY_REGISTRY.md` for the permanent ID and naming rules.

## Output

Each study run gets a unique raw directory:

```text
output\OUT__RNG001__CFG001__BRD001__RUN-YYYYMMDD-HHMMSS\
```

It contains the normal runner output plus provenance files:

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

- `combos.json` and `combos.csv`: combo, reach probability, fold/call/raise frequencies, action EVs, and mixed EV;
- `run.json`: board, convergence status, selected history/actions, and timing;
- `node.raw.json`: unmodified native current-street export;
- `bridge-transcript.jsonl`: compact IPC audit trail.

A compact analysis copy is also written to:

```text
datasets\DS__RNG001__CFG001__BRD001__RUN-YYYYMMDD-HHMMSS.csv
```

Generated `output/` and `datasets/` contents are ignored by Git by default.

## Dataset fields

`tools/collect_dataset.ps1` converts all per-board `combos.json` files into one CSV containing:

- board and combo;
- reach probability;
- fold/call/raise frequencies;
- EV of fold/call/raise in bb;
- mixed-strategy EV in bb;
- highest-frequency action;
- best-EV action;
- EV loss from forcing each pure action;
- iteration and final exploitability.

Raw showdown equity is not currently exported by the native bridge and is therefore not part of this dataset.

## Low-level runner

For ad-hoc jobs you can still call the runner directly:

```powershell
.\tsgpu-batch.cmd .\examples\config.json .\examples\boards.txt .\output\test
```

or:

```powershell
.\tsgpu-batch.ps1 .\examples\config.json .\examples\boards.txt .\output\test
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
- Current extraction targets the single-raise BB decision after BB check and the configured IP flop bet. Multiple IP bet sizes are ambiguous unless `-ExpectedBetAmount` is supplied.
- One native process per board is intentionally used for isolation. A crash on one board does not prevent later boards from running.
- `RNG001` is sourced from the bundled TexasSolverGPU range library. Its public upstream provenance is not documented, so it must not be described as a GTO Wizard range without separate evidence.

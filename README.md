# TexasSolverGPU production batch runner v012

This package automates the original TexasSolverGPU v0.2.0 native GPU/CUDA
engine through its WebView2 bridge. It does not implement or substitute a poker
solver.

## Install

Keep the runner folder next to the untouched solver folder:

```text
D:\downloads\
  TexasSolverGpu-v0.2.0-windows-x64\
  tsgpu-batch-v012\
```

The runner automatically uses:

```text
..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe
```

## Run

From the runner folder:

```powershell
.\tsgpu-batch.cmd .\examples\config.json .\examples\boards.txt .\output
```

or directly:

```powershell
.\tsgpu-batch.ps1 .\examples\config.json .\examples\boards.txt .\output
```

There is no 20-board limit. Blank lines and lines beginning with `#` in the
board file are ignored. Each remaining line must contain one three-card flop,
for example `3d 6h Kd`.

The optional top-level configuration section is:

```json
"runner": {
  "maxIterations": 1000,
  "targetExploitability": 0.5
}
```

When omitted, these same defaults are used. For diagnostics only, run the PS1
with `-ShowHostWindow`. The default is to suppress windows belonging to the
exact `TexasSolverGpu_131.exe` path while leaving WebView2 and CUDA active.

## Output

The output root contains `batch-summary.json` and `batch-summary.csv`. Every
board has a numbered subdirectory with:

- `combos.json` and `combos.csv`: combo, reach probability, fold/call/raise
  frequencies, action EVs, and mixed EV;
- `run.json`: board, convergence status, selected history/actions and timing;
- `node.raw.json`: unmodified native current-street export;
- `bridge-transcript.jsonl`: compact IPC audit trail.

## Limitations

- Windows and the Microsoft Edge WebView2 Runtime are required.
- The original v0.2.0 solver installation and a compatible NVIDIA/CUDA setup
  are required.
- Current extraction targets the single-raise BB decision after BB check and
  the configured IP flop bet. Multiple IP bet sizes are ambiguous unless
  `-ExpectedBetAmount` is supplied.
- One native process per board is intentionally used for isolation. A crash on
  one board does not prevent later boards from running.

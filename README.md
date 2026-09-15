# TexasSolverGPU batch runner

Windows batch automation for **TexasSolverGPU v0.2.0 x64**. It keeps the original CUDA/GPU engine and uses only verified WebView2 bridge methods.

## Production model

For each flop the runner:

- launches `TexasSolverGpu_131.exe` with the host window suppressed;
- initializes the configured ranges, pot, stack and betting tree;
- performs one GPU solve and waits for convergence;
- applies the configured action history;
- exports one selected current-street decision with `solver.export.currentStreet`;
- writes native JSON, combo JSON/CSV, a bridge transcript and run metadata.

This is the supported stock workflow. The runner does **not** claim to save or reload the complete solved postflop tree. To collect another branch later, run a separate job with another `runner.decisionNode`.

## Quick start

Keep this repository beside `TexasSolverGpu-v0.2.0-windows-x64`, then run:

```powershell
.\tsgpu-batch.cmd .\example\config.json .\example\boards.txt .\output\example-five-flops
```

The example contains five flops and one IP flop bet size, 33%. Its `runner` block selects `BB_RESPONSE` and verifies the expected native amounts: bet 18, raise 73.

Command-line options override matching `runner` values from JSON. The relevant settings are:

```json
{
  "runner": {
    "maxIterations": 1000,
    "targetExploitability": 0.5,
    "decisionNode": "BB_RESPONSE",
    "expectedBetAmount": 18,
    "expectedRaiseAmount": 73
  }
}
```

Supported UTG-vs-BB flop presets are `BB_FIRST`, `UTG_CBET`, `BB_RESPONSE`,
`UTG_VS_CHECK_RAISE`, `UTG_VS_DONK`, and `BB_VS_DONK_RAISE`. Existing
UTG-vs-BTN presets remain `UTG_OOP_CBET`, `BTN_RESPONSE`, `BTN_STAB`, and
`UTG_RESPONSE`. BTN-vs-BB adds explicit `BTN_CBET`, `BB_VS_BTN_CBET`,
`BTN_VS_CHECK_RAISE`, `BTN_VS_DONK`, and `BB_VS_BTN_DONK_RAISE` aliases;
`BB_FIRST` is shared. `expectedBetAmount` and `expectedRaiseAmount` are safety
checks; use `0` to disable a check.

## Output

Each numbered board directory contains `run.json`, `node.raw.json`, `combos.json`, `combos.csv`, and `bridge-transcript.jsonl`. The output root contains `batch-summary.json` and `batch-summary.csv`. CSV is the canonical resume/parsing summary and is published first. If another application locks the raw JSON, the batcher writes a timestamped `batch-summary-*.json` fallback and continues; the compact dataset still receives a fresh canonical JSON summary.

`-Resume` reuses only boards with both `run.json` and `combos.json` and verifies that the decision preset matches.

See `example/README.md`, `docs/BASELINE.md`, `docs/BRIDGE_SCHEMA.md`, and `docs/HISTORY.md`.

## Active studies

`studies/STU001__RNG001_UTG-vs-BB__5FLOP_50-50/` is the first reproducible
performance study. It uses RNG001, five canonical BRD001 flops, one 50% normal
bet size on flop and turn, and writes raw output locally under `output/` plus
compact tracked reports under `datasets/`.

`studies/STU002__RNG001_UTG-vs-BB__BRD001_FLOP6/` defines six independent
stock jobs that cover the complete normal-action UTG-vs-BB flop interaction
over BRD001. Each board/branch still performs its own solve and exactly one
current-street export.

`studies/STU004__RNG002_UTG-vs-BTN__BRD001_FLOP4/` is the production form of
the STU003 pilot: the same four selected UTG-vs-BTN flop decisions over all
286 canonical BRD001 flops.

`studies/STU005__RNG003_BTN-vs-BB__BRD001_FLOP6/` defines the same complete
six-branch normal-action flop interaction for BTN open 2.5 bb versus BB call.
Its config is prepared and validated from bundled RNG003 ranges; GPU results
are not part of the preparation commit.

STU002 and STU004 completed compact datasets each feed one approved
human-strategy workbook: 12 hand rows by ten final flop categories. One local
Python command creates the machine-readable outputs, audits and workbook
without Codex or `@oai/artifact-tool`. The exact range provenance, classifier
priority, BDFD cell rule, aggregation rule, EV audit and generic rebuild
command are fixed in `docs/FLOP_STRATEGY_WORKFLOW.md`. The separately reviewed
human-simplification method is documented in
`docs/HUMAN_STRATEGY_SIMPLIFICATION.md` and is not applied automatically. The
completed STU003 pilot was removed from the active tree after STU004
superseded it; Git history preserves the proof.

The exact human-table search, subgroup-skew audit and GPT-6 Astra review
contract are in `docs/HUMAN_STRATEGY_SIMPLIFICATION.md`. The approved STU002
BB-defense worked example is in `docs/BB_DEFENSE_SIMPLIFICATION.md`; the approved
UTG responses to the check-raise and donk branches are in
`docs/UTG_CHECK_RAISE_RESPONSE_SIMPLIFICATION.md` and
`docs/UTG_DONK_RESPONSE_SIMPLIFICATION.md`; the approved BB response to the
donk-raise is in `docs/BB_DONK_RAISE_RESPONSE_SIMPLIFICATION.md`; the approved
UTG response to the BTN stab and BTN response to the UTG c-bet are in
`docs/UTG_STAB_RESPONSE_SIMPLIFICATION.md` and
`docs/BTN_CBET_RESPONSE_SIMPLIFICATION.md`; the approved UTG c-bet against BB
is in `docs/UTG_CBET_VS_BB_SIMPLIFICATION.md`; the approved UTG c-bet against
BTN is in `docs/UTG_CBET_VS_BTN_SIMPLIFICATION.md`; the approved BTN stab after
UTG checks is in `docs/BTN_STAB_VS_UTG_SIMPLIFICATION.md`. A concise runner and table
evolution is in `docs/BATCHER_EVOLUTION.md`; active
repository-changing work is recorded in `docs/WORK_LOG.md`. Script ownership
and the sole strategy entry point are summarized in `scripts/README.md`.

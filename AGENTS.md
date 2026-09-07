# Instructions for working with this repository and TexasSolverGPU

This file is the handoff guide for a new ChatGPT conversation. Read it **before changing anything** in this repository.

Scope of this file: **repository operation, runner development, solver execution, datasets, CI, and debugging only**. Poker strategy conclusions and human simplification rules are intentionally not documented here.

## 1. What this repository is

This repository is a production batch/analysis wrapper around the **original TexasSolverGPU v0.2.0 Windows x64 solver**.

The repository does **not** implement a poker solver. Do not replace or reimplement TexasSolverGPU unless the user explicitly asks for that.

The native executable is:

```text
TexasSolverGpu_131.exe
```

Known user installation:

```text
D:\current\manuals\покер\sotf\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe
```

The production runner normally expects the repository directory and the untouched solver directory to be siblings. It can also use `-SolverExe` or `TSGPU_SOLVER_EXE`.

The user wants the workflow to be command-line/batch driven. **Do not send the user into the TexasSolverGPU GUI** unless automation is genuinely impossible and you have first explained why. In particular, do not rely on the GUI memory-estimate button; it has been unreliable/crashy.

## 2. What to read at the start of a new chat

When the user gives the repository link and says there is an instruction, do this immediately:

1. Read this `AGENTS.md` completely.
2. Read `README.md`.
3. Read `docs/STUDY_REGISTRY.md`.
4. Read the specific runner/scripts/configs relevant to the requested task.
5. Read the latest dataset/manifest only if the task depends on solved data.

Do not answer from remembered old code if the repository can be read. The remote repository is the source of truth.

## 3. Git/GitHub working rules

The working branch is `main` unless the user says otherwise.

The user has explicitly authorized direct commits/pushes for this repository. **Do not ask for confirmation before each normal repo edit or push.** Make the change, validate it, and report the commit.

Before modifying an existing file:

- fetch/read its current remote contents;
- preserve current behavior unless the requested task changes it;
- do not overwrite newer user changes with an older remembered version.

For behavioral changes to the runner:

- keep existing launchers/backward compatibility where practical;
- add/update automated checks;
- run the relevant GitHub Actions workflow;
- inspect the actual job logs, not only the green/red status;
- fix failures before telling the user the change is ready.

Do not ask the user to manually edit source files, JSON, PowerShell, CMD, or YAML when you can make the repo change yourself.

## 4. Division of labor: assistant vs user PC

### The assistant should do

- inspect and modify repository code;
- create/update configs, launchers, analysis scripts, docs, and CI workflows;
- commit/push changes;
- use GitHub Actions for Python/static analysis whenever possible;
- inspect workflow logs and debug failures;
- analyze versioned datasets already present in `datasets/`;
- give the user the shortest exact command needed when a real GPU solve must be run locally.

### The user should normally only need to do

Actual TexasSolverGPU solves require the user's Windows/NVIDIA machine. When a new solve is needed, tell the user exactly what to run, preferably as a single launcher command from the repository root, for example:

```powershell
.\scripts\RUN__CFG001__NOD002__BRD001.cmd
```

If their local checkout may be stale, first tell them:

```powershell
git pull
```

After the solve, the versioned analysis dataset and its manifest must get back into the repository before server-side analysis can continue. Prefer asking the user to push the generated files or provide them, rather than asking them to inspect solver internals manually.

Do **not** offload Python analysis or code debugging to the user when GitHub Actions can do it.

## 5. Permanent study IDs and invariants

Study IDs are immutable. Never silently change what an existing ID means. If ranges, board family, tree semantics, or decision-node semantics change, create a new ID or a new versioned definition.

Current permanent baseline:

### `RNG001`

- 6-max NLHE cash, 100bb;
- UTG open 2.5bb;
- BB call;
- ranges come from the **TexasSolverGPU v0.2.0 bundled 6-max range library**.

Do **not** call `RNG001` a GTO Wizard range. Its public upstream provider is not documented.

### `BRD001`

- 286 canonical unpaired rainbow flops;
- one representative for every three-distinct-rank combination;
- `C(13,3) = 286`.

Do not replace or mutate `BRD001` when adding future board families. Create a new board-set ID.

### `CFG001`

Spot/tree:

```text
UTG open 2.5bb -> BB call
flop: BB Check -> UTG Check or Bet 33%
after Bet: BB Fold / Call / XR60
```

Native money scale is x10:

```text
startingPot     = 55   # 5.5bb
effectiveStack = 975  # 97.5bb
UTG flop bet    = 18   # 1.8bb
BB raise        = 73   # 7.3bb
```

### `CFG002`

Same spot/tree as `CFG001`, except UTG flop bet is 75%.

Native amounts:

```text
UTG flop bet = 41
BB raise     = 123
```

`CFG002` is intentionally derived from `CFG001`; do not duplicate the full two 1326-entry range arrays unnecessarily.

### Solver defaults

Unless a registered config says otherwise:

```text
maxIterations        = 1000
targetExploitability = 0.5
```

## 6. Decision-node semantics

Decision-node IDs select which solved node is exported; they do not redefine the underlying tree.

### `NOD001 / BB_RESPONSE`

Acting player: BB.

Export after:

```text
BB Check -> UTG configured Bet
```

Actions:

```text
Fold / Call / Raise
```

Historical CFG001/CFG002 BB-response launchers may omit `NOD001` from output filenames, but their semantics are still `BB_RESPONSE`.

### `NOD002 / UTG_CBET`

Acting player: UTG.

Export after:

```text
BB Check
```

and **before** applying the UTG bet.

Actions semantically are:

```text
Check / Bet 33%
```

For CFG001 the expected native wager amount is 18.

Important native quirk: TexasSolverGPU v0.2.0 may label the first IP wager after OOP check as either:

```text
Bet 18
```

or:

```text
Raise 18
```

The runner intentionally accepts both as the same semantic UTG c-bet. **Do not remove this alias handling.** The same principle applies when validating equivalent native first-wager labels in future nodes.

## 7. Primary launchers

From the repository root:

```powershell
.\scripts\RUN__CFG001__BRD001.cmd
.\scripts\RUN__CFG002__BRD001.cmd
.\scripts\RUN__CFG001__NOD002__BRD001.cmd
```

Meaning:

- CFG001 BB response to B33;
- CFG002 BB response to B75;
- CFG001 UTG c-bet node after BB checks.

For ad-hoc low-level runs, use the production `tsgpu-batch.ps1` / `tsgpu-batch.cmd` interfaces described in `README.md` rather than inventing GUI steps.

## 8. Output and versioning

Raw run directories are written under `output/` and are ignored by Git.

Completed analysis datasets under `datasets/` are intentionally versioned.

Typical UTG c-bet names:

```text
output/OUT__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS/
datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS.csv
datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-YYYYMMDD-HHMMSS.manifest.json
```

Every serious study run must remain reproducible. Preserve/copy the effective inputs and manifest data rather than relying on an unrecorded local GUI state.

Expected raw run artifacts include:

```text
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

Per-board debugging artifacts include:

```text
combos.json
combos.csv
run.json
node.raw.json
bridge-transcript.jsonl
```

## 9. Dataset semantics

### BB response dataset

Expected fields include:

- board, combo, reach probability;
- fold/call/raise frequencies;
- EV of each action in bb;
- mixed-strategy EV;
- highest-frequency action;
- best-EV action;
- EV loss from forcing each pure action;
- iteration and final solver exploitability.

### UTG c-bet dataset

Expected fields include:

- `board`;
- `combo`;
- `reach_probability`;
- `check_frequency`;
- `bet_frequency`;
- `ev_check_utg`;
- `ev_bet_utg`;
- `mixed_ev_utg`;
- `best_ev_action`;
- `best_ev_utg`;
- `highest_frequency_action`;
- `highest_frequency`;
- `loss_if_check_utg`;
- `loss_if_bet_utg`;
- iteration;
- final exploitability.

EV/loss values are in **bb**, not native x10 units.

Important interpretation rule: `loss_if_*` is local regret versus the opponent strategy in the solved equilibrium tree. It is useful for screening simplifications, but it is **not** by itself the exploitability of a manually altered strategy after the opponent adapts.

## 10. Debugging order

When a batch run fails, do not guess from the UI. Inspect artifacts in this order:

1. `error.json` if present;
2. per-board `run.json`;
3. `batch-summary.json` / `batch-summary.csv`;
4. `bridge-transcript.jsonl`;
5. `node.raw.json`;
6. relevant worker/runner PowerShell source;
7. only then consider whether native solver behavior itself needs additional probing.

Keep the original TexasSolverGPU installation untouched. Fix automation in this repository unless there is strong evidence that a native binary/config issue is the cause.

A failure on one board should not stop the entire batch; the runner intentionally isolates boards in separate native processes.

## 11. How to make runner changes

For a new node/config/study family:

1. define exact semantics first;
2. create a new immutable ID when required;
3. add the config/derived config and launcher;
4. add expected native action validation;
5. update dataset collection/schema deliberately;
6. write a manifest with IDs and hashes;
7. add automated tests/CI for the new behavior;
8. run CI and inspect logs;
9. only then ask the user to run the real GPU batch if solved data is needed.

Do not change several unrelated runner behaviors at once. Prefer small, auditable commits.

When changing parsers/exporters, preserve raw native payloads (`node.raw.json`) so a later bug can be diagnosed without rerunning all 286 boards.

## 12. What to tell the user

Keep operational instructions short.

When no local GPU solve is needed, do the repo work yourself and tell the user:

- what changed;
- the commit SHA;
- whether CI passed;
- any important compatibility consequence.

When a local GPU solve is needed, tell the user exactly:

1. whether to `git pull`;
2. the single launcher command to run;
3. what output/dataset should appear;
4. what file(s) need to be pushed/provided afterward.

Do not make the user reconstruct command lines, edit configs, click through the GUI, or infer which dataset you need.

## 13. Current production principle

The desired end state is a robust headless interface conceptually equivalent to:

```text
tsgpu-batch.exe config.json boards.txt output\
```

It does **not** have to be an `.exe`; PowerShell/CMD is acceptable. The important requirements are:

- config + board list in;
- unattended native solve;
- robust polling/retry/stop behavior;
- deterministic per-board artifacts;
- one consolidated dataset;
- `error.json` on board failure;
- no manual GUI interaction.

Preserve that principle when extending the repository.


### Additional registered UTG-vs-BTN nodes

The authoritative current registry is `docs/STUDY_REGISTRY.md`. For `RNG002 / CFG003 / BRD001`:

- `NOD003 / UTG_OOP_CBET`: UTG root Check/Bet 33%;
- `NOD004 / BTN_RESPONSE`: BTN Fold/Call/Raise after UTG root Bet 33%; expected native UTG wager 21 and BTN Raise 128;
- `NOD005 / BTN_STAB`: BTN Check/Bet 33% after UTG root Check; expected native BTN wager 21.

BTN datasets use `*_btn` EV/loss field suffixes. Do not relabel these nodes as UTG or BB decisions.

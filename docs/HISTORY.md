# Project history

This file records what was done so future work does not repeat discarded approaches. Historical outputs are intentionally absent from active `main`.

## 1. Working runner generation through v015

The project automated `TexasSolverGpu_131.exe` from TexasSolverGPU v0.2.0 through its WebView2 bridge.

By the state represented by commit:

`bec0b758fe7957a45d028f1adaa2a5252ff0598a`

the runner had a proven `v015-production` core that could start the desktop runtime headlessly, suppress its window, initialize/allocate, solve, poll status, navigate action histories and export a selected current-street strategy node.

That commit is the source of the worker/batch files retained in the clean baseline.

## 2. First research cycle — discarded outputs

The old repository calculated seven node-specific datasets over BRD001, covering UTG-vs-BB and UTG-vs-BTN flop decisions/responses. It also accumulated strategy reports and universal-strategy experiments EXP-001 through EXP-004.

Those files were useful for learning how the solver/runner behaved, but the user later decided that none of these calculated outputs should remain in active `main`. They are recoverable from Git history if ever needed.

No old dataset or strategy result is active evidence now.

## 3. Architectural problem discovered

The old workflow often solved the same configured postflop tree again merely to export another decision node. TexasSolverGPU had already solved the configured tree, while the runner persisted only one selected node.

That wastes GPU time and prevents later turn/river analysis from the same solution.

A second issue was identified when alternative flop bet sizes were studied in separate trees: branch ranges differ when a sizing exists as the only bet versus when it competes with other sizes. This made the old separate-size datasets unsuitable as branches of one common strategy.

The durable architectural requirement became:

**solve the configured postflop tree once, persist the complete solved strategy tree, analyze arbitrary nodes later without another GPU solve.**

## 4. 2026-09-08 full-tree reset attempt — rejected implementation

A new `v020` generation was created after the first research-cycle cleanup. It introduced STU001/STU002-style full-tree study contracts and tried to persist the whole solution.

However, the actual complete-tree native export mechanism had not been identified. The experimental worker instead probed plausible names such as `solver.export.fullTree`, `solver.export.fullStrategy`, `solver.dump.strategy`, and similar endpoints, then accepted JSON heuristically if it appeared to contain turn/river structure.

The user correctly challenged this as a workaround rather than a real implementation. The experiment was abandoned before a production study was launched.

Relevant historical commits include the clean/full-tree experiment sequence around:

- `2ac68b65dbffa63a74872f829a3100fecc57ca6f`;
- `af522a65f2db4e3ebee192b99ac3d95577e65521`;
- `772a8034060c47ae2e2f9eaf718bf324123fed8d`.

These commits remain history only. Their guessed exporter logic is not part of the baseline.

## 5. Clean baseline decision

The repository was then intentionally reduced to source inputs, documentation and the proven v015 runner core.

Removed from active `main`:

- all datasets;
- all analysis/results;
- all study definitions/launchers;
- all old configs except one smoke fixture;
- all strategy/report tools;
- the v020 guessed full-tree exporter.

Retained:

- RNG001 and RNG002 source ranges;
- BRD001 source flop list;
- one smoke fixture;
- `Range-Utils.ps1`;
- v015 worker/batch core;
- engineering history/instructions and static CI.

## 6. Next step

A separate runner-development effort should identify the **real** TexasSolverGPU complete-strategy save/export mechanism from the installed runtime/frontend and prove it on one board before any new large study is created.

## 7. 2026-09-08 exhaustive stock-API proof

The installed application, frontend bundle, bridge behavior, public GPU repository and related viewer/serializer code were inspected. No monolithic native full-tree save/load bridge method was found.

A complete one-board reconstruction was nevertheless proven using only verified stock operations:

- `solver.history.apply`;
- `solver.cards.possible` at chance boundaries;
- `solver.export.currentStreet` for every reachable street fragment.

For flop `6s As 8c`, one GPU solve produced a complete graph with 1 flop fragment, 196 turn fragments and 32,928 river fragments (33,125 total). Offline validation found 175,327 action nodes, 690 chance nodes, 250,589 terminal nodes and zero missing links.

The archive was 589,025,997 bytes and extraction took 1,097,838 ms (~18.3 minutes), while the solve itself took about 4.5 seconds. This proved data accessibility but also proved that exhaustive fragment persistence is not production-worthy for a 286-board workload.

A follow-up WIP attempted internal JavaScript traversal, request pipelining, dictionary-based compact JSON and OPFS streaming. Representative reconstructed payloads exactly matched fresh native `currentStreet` responses. Storage and external round trips improved, but native per-fragment exports remained the dominant cost and the design still required tens of thousands of bridge calls.

## 8. Final production decision

The user selected the stock selected-branch workflow as the product boundary. Commit `23fa871` and its uncommitted compact-export follow-up were removed from the active WIP content; revert commit `977b230` restored the proven v015/current-street baseline while retaining the investigation in Git history.

The production runner now intentionally does:

**one board -> one GPU solve -> one configured decision history -> one stock current-street export.**

No guessed method, exhaustive full-tree traversal, custom tree archive or offline full-tree loader is part of the supported path.

One useful usability improvement from the work was retained: `runner.decisionNode`, `runner.expectedBetAmount`, and `runner.expectedRaiseAmount` can be stored in the input JSON, while explicit command-line arguments still override them. This makes `tsgpu-batch.cmd config.json boards.txt output\` a complete reproducible invocation.

The `example/` directory documents and exercises five flops for the UTG 2.5bb open / BB call spot with pot 55, effective stack 975, IP flop bet 33%, OOP flop bet disabled, and OOP raise 60%. The separate `smoke/` fixture remains one board.

The final Windows/NVIDIA verification used the exact three-argument command from `example/README.md`. All five boards completed successfully in 52.6 seconds total. Every board produced the five documented output files, used exactly one `solver.solve.start` and one `solver.export.currentStreet`, selected `BB_RESPONSE`, and returned `Fold / Call / Raise 73`. No guessed/full-tree bridge call appeared in any transcript.

## 9. STU001 timing proof and STU002 flop study

STU001 introduced the agreed single-size UTG-vs-BB abstraction: 50% flop and
turn bets, 75% OOP / 100% IP river bets, native raise size 60, and one normal
raise after the opening bet. TexasSolver counts the opening bet in
`maxRaiseNumber`, so this is encoded as `maxRaiseNumber=2`.

A clean five-board Windows/NVIDIA run completed 5/5 in 117.561 seconds. This
established an approximate two-hour runtime for one selected decision over all
286 BRD001 flops.

STU002 then defined six independent selected-branch jobs for the complete
normal-action flop interaction: BB first action, UTG after BB check, BB after
UTG c-bet, UTG after BB check-raise, UTG after BB donk, and BB after UTG raises
the donk. These presets use only `solver.history.apply`,
`solver.node.actionsAfter`, and one `solver.export.currentStreet` after a fresh
solve. Turn and river remain in the solve as continuation abstractions but are
not exported or analyzed by STU002.

The first 286-board `BB_FIRST` run exposed another transient WebView2 startup
signature: the injected page helper could briefly be undefined, producing a
`requestObject` error. Batch retry now treats that exact undefined-helper case
like the already-known DevTools startup race and allows up to three startup
attempts. STU002 resume reporting preserves the prior attempt's board-time sum
and adds only the retried boards, rather than reporting the short resume wall
time as the duration of the whole study.

## 10. STU002 CSV serialization correction

Post-run validation of the first complete `BB_FIRST` dataset found that
`combos.json` was correct but `combos.csv` contained `OrderedDictionary`
metadata instead of combo fields. Combo rows are now emitted as
`PSCustomObject` values, CSV numeric serialization uses invariant culture, and
STU002 aggregation reads the canonical per-board `combos.json` with a
combo-count check. The completed JSON outputs did not require another GPU solve;
the affected CSV files were regenerated from them.

## 11. STU002 human-strategy standard

The first strict table retained too many base/draw combinations for practical
study. An initial data-backed merge produced 13 displayed hand rows. A later
raw-frequency audit simplified the unmade part without translating displayed
labels back into invented frequencies. The active table has 11 rows: seven
made-hand bases, OESD, Gutshot, 2 overcards plus BDFD, and Air. Made hands keep
their base; for unmade hands direct draws take priority, and BDFD stays
explicit only with exactly two overcards and no direct straight draw.

Two later attempts tried to smooth action changes horizontally across B13.
They were rejected after distorting important strategic structure, including
BB low-board donks and UTG raise frequencies. Their scripts and generated
outputs were removed from active `main`; Git history preserves them if they
are ever needed for diagnosis.

The accepted replacement does not smooth displayed labels. It recalculates
cells directly from source solver combo frequencies at two flop resolutions:
B13 and eight broader, mutually exclusive categories. Both use the same 11
hand rows, a pure threshold strictly above 65%, otherwise an exact top-two
50/50 mix. EV is a reach-weighted local-regret audit only. The complete active
contract is now `docs/FLOP_STRATEGY_WORKFLOW.md`.

## 12. STU003 pilot and STU004 production study

STU003 validated the RNG002 UTG-open / BTN-call configuration and four selected
flop decisions on five boards. STU004 expanded the identical configuration to
all 286 BRD001 flops. After transient WebView2 failures were retried with the
standard resume path, all four branches completed: 1,144/1,144 boards, zero
failed, 286 PASS validations per branch, one solve and one current-street
export per board, and zero forbidden full-tree calls.

The successful compact STU004 evidence became active input for the same two
human tables as STU002. The classifier and workbook builders were generalized
instead of copied. Once STU004 was complete, the superseded STU003 package and
compact pilot evidence were removed from active `main`; Git history preserves
them. STU004 launchers use `scripts/run-flop-study-*.ps1` directly.

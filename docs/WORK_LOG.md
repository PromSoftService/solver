# Work log

This file records each repository-changing task before implementation and closes it after validation and push. It is intentionally concise.

## 2026-09-14 — Human-strategy workflow consolidation

Status: STARTED

Starting point:

- branch `main` is clean;
- local `HEAD` and `origin/main` are both `11da98985235358d7f3eb884e4fe057694960213`;
- no active Local Desktop Commander sessions;
- no solver or Excel process is running;
- no GPU solve is authorized for this task.

Plan:

1. document the reproducible human-table method, subgroup audits and Astra review contract;
2. record the batch runner and strategy-table evolution in a short dedicated history;
3. decide whether the untracked human-candidate workbooks are canonical, reproducible outputs or disposable experiments;
4. reduce the strategy scripts to one supported generator path and remove only proven obsolete artifacts;
5. rebuild STU002 and STU004 from tracked datasets, validate code and workbooks, record results;
6. review the final diff, commit and push `main`.

Completion, checks and pushed commit will be appended below.


Completion:

Status: VALIDATED — READY TO COMMIT

Changed:

- expanded the exact human-table, flop-partition, subgroup-skew and Astra review contract;
- added the concise batcher evolution and strategy-script ownership documents;
- made the start/validate/report/commit/push lifecycle mandatory in `AGENTS.md`;
- removed the superseded tracked `scripts/generate-stu003-config.mjs`;
- removed two ignored, noncanonical experimental candidate workbooks and Python cache;
- kept the single universal baseline generator and preserved all studies, ranges,
  boards, tracked datasets and raw solver-output directories.

Validation:

- fetched `origin/main` and worked from base `11da989`;
- compiled all three Python strategy files;
- parsed every tracked PowerShell file;
- checked and regenerated the STU004 config with no tracked diff;
- rebuilt STU002: 598 populated cells, 13 BDFD cells, 8 sheets, 0 formula errors;
- rebuilt STU004: 406 populated cells, 5 BDFD cells, 6 sheets, 0 formula errors;
- confirmed no diff in canonical datasets after rebuild;
- `git diff --check` passed;
- confirmed no Excel, TexasSolverGPU or active Local Desktop Commander session;
- did not run a GPU solve.

Remaining limit: human candidates are documented research, not generated output,
until one exact complete version is explicitly approved and stored as
machine-readable policy.


## 2026-09-14 — STU004 BTN versus UTG c-bet human table

Status: STARTED

Starting point:

- branch `main` is clean;
- local `HEAD` and `origin/main` are both `139145176083aee9f5ec1015827bd807937a82eb`;
- source branch is `STU004 / 03_BTN_AFTER_CBET`;
- existing tracked `combos.csv` is the only solver-data input;
- no Excel, TexasSolverGPU or active Local Desktop Commander session;
- no GPU solve and no canonical workbook edit are authorized.

Plan:

1. reproduce the baseline classifier, cell aggregation and branch metrics;
2. search the smallest deterministic flop partitions and allowed pure/50-50 policies;
3. audit node frequencies, local regret, tails and action-range composition;
4. inspect ABB/BBB, BDFD, pair-with-draw, kicker and support subgroups;
5. send the Pareto candidates and worst errors to GPT-6 Astra for independent critique;
6. locally reproduce any accepted Astra finding;
7. report one recommended Markdown table for user approval without changing generation.


Completion:

Status: ANALYZED — AWAITING USER APPROVAL

Result:

- analyzed all 61,270 active combo rows from the tracked STU004 `03_BTN_AFTER_CBET` export;
- tested 36 deterministic flop partitions and 1,285 compact policy refinements;
- selected the five already-established classes: `Axx`, `B[Q-8]x`, `B[7-3]x`,
  `[9-2]x con` and `[9-2]x dis`;
- reduced the proposed teaching table from 100 populated baseline cells to 56;
- independently reviewed the candidate with GPT-6 Astra and reproduced every
  accepted correction against the local combo EV data;
- removed the unsupported `F/R` choice from the negligible-reach
  `Low pocket pair / [9-2]x con` cell in favor of lower-regret `F/C`.

Audit:

- solver F/C/R: 34.8385% / 52.4340% / 12.7276%;
- candidate F/C/R: 34.4556% / 53.6772% / 11.8672%;
- mean fixed-opponent reach-weighted local regret: 0.0179813 bb;
- root-weighted value of that audit: 0.00392183 bb;
- P99 loss: 0.338093 bb; reach above 0.10 bb: 5.3988%;
- hand-row mean absolute frequency error: 5.3239 percentage points;
- raise-range hand-composition TVD: 0.16887.

No GPU solve was run. No solver export, study, range, board, canonical policy,
generator or workbook was changed. Promotion into generated Excel remains blocked
until the exact Markdown table is approved by the user.


## 2026-09-14 — STU002 UTG versus BB check-raise human table

Status: STARTED

Starting point:

- branch `main` is clean;
- local `HEAD` and `origin/main` are both
  `790853764e0f76a149beba771e74cae6f78c6341`;
- source branch is `STU002 / 04_UTG_AFTER_CHECK_RAISE`;
- source export is the tracked `20260909-003912Z/combos.csv`;
- the node contains only FOLD and CALL actions;
- no GPU solve and no canonical workbook edit are authorized.

Plan:

1. reproduce the baseline classification and node metrics;
2. compare compact familiar flop partitions with pure/50-50 F/C policies;
3. audit hand-row bias, BDFD dependence, local combo EV and loss tails;
4. ask GPT-6 Astra to review the Pareto candidates and material exceptions;
5. reproduce the accepted findings locally;
6. report one Markdown table for user approval without changing generation.

Status: ANALYZED — AWAITING USER APPROVAL

Result:

- evaluated 36 compact partitions against the tracked combo export;
- selected seven exhaustive classes: `ABB` (6), `A[K/Q]x` (16),
  `A[J-T]x` (16), `A[9-2]x` (28), `BBB` (4), `Bxx` (160),
  and `[9-2]xx` (56);
- reduced the table from 101 populated baseline cells to 69;
- retained `BDFD` only where the solver continuation is carried by the
  backdoor-flush subset;
- added `SUITED` for `Gutshot / A[J-T]x`: call suited hole cards, fold offsuit;
- independently reviewed the candidate with GPT-6 Astra and reproduced its
  requested `Gutshot / Bxx: C -> C/F` control locally.

Audit:

- solver F/C: 39.2341% / 60.7659%;
- candidate F/C: 38.2314% / 61.7686%;
- mean fixed-opponent reach-weighted local regret: 0.0206200 bb;
- root-weighted value of that audit: 0.00140393 bb;
- P99 loss: 0.580688 bb; maximum combo loss: 2.87821 bb;
- hand-row mean absolute frequency error: 5.3482 percentage points;
- call-range hand-composition TVD: 0.05327.

The Astra control was rejected: `Bxx` is 60.89% of Gutshot reach, and changing
it to `C/F` moved total F/C to 42.3425% / 57.6575%, raised mean regret to
0.0741972 bb, P99 to 1.77075 bb and maximum loss to 4.10376 bb. `C` therefore
remains the supported simplification despite the visible Gutshot overcall.

No GPU solve was run. No solver export, study, range, board, canonical policy,
generator or workbook was changed. Promotion remains blocked until user approval.


## 2026-09-14 — STU002 UTG versus BB donk human table

Status: STARTED

Starting point:

- local `main` is clean and one documentation commit ahead of `origin/main`;
- source branch is `STU002 / 05_UTG_AFTER_DONK`;
- history is `BB Donk 50%`; UTG chooses FOLD/CALL/RAISE 60 native;
- tracked source export is `20260909-003948Z/combos.csv`;
- no GPU solve and no canonical workbook edit are authorized.

Plan: reproduce the baseline, search compact exhaustive flop partitions, audit
hand-row and action-range composition plus combo EV/tails, obtain an independent
GPT-6 Astra review, reproduce accepted tests locally, and report one Markdown
candidate for user approval.

Status: ANALYZED — AWAITING USER APPROVAL

Result:

- evaluated 36 compact exhaustive partitions;
- selected five familiar classes: `Axx` (66), `B[Q-8]x` (104),
  `B[7-3]x` (60), `[9-2]x dis` (40), `[9-2]x con` (16);
- reduced the branch from 103 populated baseline cells to 56;
- retained one conditional selector: `Air / Axx = BDFD`;
- GPT-6 Astra independently reviewed the candidate and requested four bounded
  one-cell controls; every control was reproduced locally.

Accepted control:

- `OESD / B[7-3]x: R -> R/C` reduced OESD over-raising, mean regret,
  P99 and raise-composition error.

Rejected controls:

- both Weak-pair raise additions selected locally unsupported raises (solver
  raise 9.6% and 0.9% in the tested cells);
- restoring `Third pair / [9-2]x dis = C/R` increased row error to 12.46 pp.

Final audit:

- solver F/C/R: 28.0434% / 59.0276% / 12.9290%;
- candidate F/C/R: 29.5709% / 56.8135% / 13.6156%;
- mean fixed-opponent reach-weighted local regret: 0.0170222 bb;
- root-weighted value: 0.00108547 bb;
- P99 loss: 0.279847 bb; maximum combo loss: 4.55684 bb;
- reach above 0.10 / 0.25 / 0.50 bb: 4.5470% / 1.2078% / 0.1115%;
- hand-row MAE: 4.6352 pp versus 10.6935 pp for the baseline;
- action-range TVD F/C/R: 0.03229 / 0.04245 / 0.18648 versus
  0.03279 / 0.19043 / 0.52555 for the baseline.

The candidate prioritizes hand-category balance over minimum local regret:
baseline mean regret is lower at 0.0129025 bb, but its category and raise-range
composition errors are materially larger.

No GPU solve was run. No solver export, study, range, board, canonical policy,
generator or workbook was changed. Promotion remains blocked until user approval.


## 2026-09-14 — STU002 BB versus UTG raise after donk human table

Status: STARTED

Starting point:

- source branch is `STU002 / 06_BB_AFTER_DONK_RAISE`;
- history is `BB Donk 50% -> UTG Raise 60 native`; BB chooses FOLD/CALL;
- tracked source export is `20260909-024314Z/combos.csv`;
- the baseline has 91 populated cells and three BDFD selectors;
- no GPU solve and no canonical workbook edit are authorized.

Plan: reproduce the baseline, search compact exhaustive flop partitions, audit
hand-row and CALL-range composition plus combo EV/tails, obtain an independent
GPT-6 Astra review, reproduce accepted tests locally, and report one Markdown
candidate for user approval.

Status: ANALYZED — AWAITING USER APPROVAL

Result:

- evaluated 36 compact exhaustive partitions and selected five familiar classes:
  `Axx` (66), `B[Q-8]x` (104), `B[7-3]x` (60),
  `[9-2]x dis` (40), `[9-2]x con` (16);
- reduced the branch from 91 populated baseline cells to 56;
- retained `BDFD` for three Third-pair cells, `Ax` for two low-board
  two-overcard cells, and one shared `PAIR/BDFD` Gutshot rule;
- GPT-6 Astra independently accepted the action matrix and requested only exact
  coverage and selector definitions; the source was rechecked as exactly 286
  unpaired, three-distinct-rank boards before documenting the boundaries.

Class boundaries:

- `Axx`: every board containing an ace;
- `B[Q-8]x`: no ace, three distinct ranks, top rank K-T and middle
  rank Q-8;
- `B[7-3]x`: no ace, three distinct ranks, top rank K-T and middle
  rank 7-3;
- low boards have top rank at most 9 and split at rank span three:
  span above three is `dis`, span at most three is `con`.

Final audit:

- solver F/C: 41.4759% / 58.5241%;
- candidate F/C: 41.4081% / 58.5919%;
- mean fixed-opponent reach-weighted local regret: 0.0144167 bb versus
  0.0492779 bb for the baseline;
- root-weighted value: 0.000118860 bb versus 0.000406276 bb;
- P95 / P99 / maximum combo loss: 0.006982 / 0.553575 / 3.01659 bb;
- reach above 0.10 / 0.25 / 0.50 / 1.00 bb:
  2.8478% / 1.8828% / 1.0926% / 0.2215%;
- CALL-range composition TVD: 0.01993.

No GPU solve was run. No solver export, study, range, board, canonical policy,
generator or workbook was changed. Promotion remains blocked until user approval.


## 2026-09-14 — STU005 BTN vs BB study preparation

Status: STARTED

Base commit: `543921ffd747515e5ba24d0543d8966b28ed9b3d` (`origin/main` equal).

Constraints: use the bundled TexasSolverGPU v0.2.0 BTN-open/BB-call ranges; preserve BRD001 and all source data; mirror the proven STU002 six-branch single-size abstraction; do not run the GPU solver during preparation.

Plan: import and fingerprint the exact bundled ranges as RNG003, add the reproducible STU005 six-branch package, extend only the verified positional decision presets needed for BTN vs BB, validate JSON/PowerShell/boards/config histories without a solve, record results, commit and push.

Status: COMPLETED

Result:

- imported the exact bundled BTN-open/BB-call text ranges as RNG003; BTN is 550.912 weighted combos and BB is 389.82;
- added `STU005__RNG003_BTN-vs-BB__BRD001_FLOP6` with 286 BRD001 flops and six independent normal-action branches;
- added explicit BTN-vs-BB decision aliases while preserving every existing preset and the v015 solve/export boundary;
- replaced the STU004-only config builder with `scripts/generate-study-config.mjs`, which deterministically rebuilds both STU004 and STU005;
- updated baseline documentation and static CI coverage. The superseded `generate-stu004-config.mjs` was removed.

Validation:

- all 12 active PowerShell files parsed successfully;
- RNG003 tracked range bytes matched the bundled originals and both expanded to 1326 combo weights;
- STU005 config rebuilt byte-identically; STU004 rebuilt without a Git diff;
- pot 55, effective stack 975, expected flop bet 28, expected raise 95, 286 boards and six unique branches passed;
- `git diff --check` passed and no TexasSolverGPU process was started.

GPU results and human tables remain pending; this commit prepares only the reproducible study.

## 2026-09-14 — STU005 full BTN vs BB GPU run

Status: STARTED

Base commit: `d63f92d1e8d3cb40c24bd4a149b27a44b2085395` (`origin/main` equal).

Scope: run all six STU005 branches over 286 BRD001 flops (1716 independent stock solves) using RNG003 and the prepared 50% / native-60 tree. Start fresh because no STU005 output or dataset exists.

Plan: launch `run-all.ps1`, monitor local operation progress, preserve raw output under ignored `output/`, validate the completed compact dataset locally, record final timings/results, commit and push. GitHub Actions are intentionally out of scope.

Runtime startup blocker:

- the first full-run attempt and two one-board preflights selected a transient `about:blank` DevTools page and failed before `solver.init` with `requestObject` undefined;
- the runner currently falls back to the first generic page immediately instead of waiting up to its documented 45-second deadline for the TexasSolver application page.

Recovery plan: preserve the failed artifacts under `_diagnostics/`, remove the premature generic-page fallback, poll only for the verified `appassets.local/index.html` target, pass a one-board local GPU smoke, commit/push the repair, then restart STU005 fresh. GitHub Actions remain out of scope.

Recovery validation: PASS. The repaired worker waited for `https://appassets.local/index.html?desktop=1&transport=bridge`; the one-board `6s As 8c` GPU smoke completed with 508 combos and `Check / Raise 28`. No generic `about:blank` target was accepted. The full STU005 run can now restart fresh.


## 2026-09-15 — STU002 BB versus UTG c-bet five-class EV simplification

Status: COMPLETED

Base commit: `2738ee92d40bd02690b77e413fd7dd9042e7b2a9` (`origin/main` equal).

Scope: analyze only `STU002 / 03_BB_AFTER_CBET` from the tracked 106,381-row combo export. Reduce the teaching partition to `ABB`, `Axx` excluding `ABB`, `BBB`, `Bxx` excluding `BBB`, and `[9-2]xx`. Prefer low-regret pure actions; retain `C/R` only for range composition; interpret `C/F` as a deterministic solver-EV selector, never a randomizer.

Constraints: preserve all solver data and the canonical ten-category workbook; use the existing fold/call/native-60-raise EV values; do not start or disturb the active STU005 GPU solve; do not use GitHub Actions.

Plan:

1. reproduce the branch classifier, reach weights and baseline audit from tracked data;
2. enumerate five-class pure and 50/50 C/R candidates plus deterministic C/F selectors;
3. compare average and tail regret, overcall/overfold, total frequencies and CALL/RAISE composition;
4. send compact metrics and worst subgroups to GPT-6 Astra, reproduce accepted checks locally;
5. save a separate machine-readable candidate and audit without changing the canonical generator/workbook;
6. validate, close this log entry, commit and push `main`.


Result:

- added `scripts/analyze-human-bb-response.py` and reproduced a separate
  five-class candidate plus JSON/CSV audits under
  `analysis/human-5/03_BB_AFTER_CBET`;
- verified 106,308 reach-positive rows, exact source mixed-EV reproduction,
  and flop counts 6/60/4/160/56;
- solver F/C/R is 47.8993/39.0930/13.0076%; candidate F/C/R is
  49.0865/39.2677/11.6458%;
- mean source-mix loss is 0.008601 bb; mean oracle regret is 0.010608 bb;
  weighted P95/P99 is 0.031112/0.234361 bb;
- deterministic C/F selectors were audited separately; the AK-only Air
  exception improves mean loss by about 0.00400 bb for only 0.48 percentage
  points moved from FOLD to CALL;
- GPT-6 Astra independently accepted the result as a locally EV-audited human
  compromise. The Gutshot/Bxx C/R tail remains documented; no unmeasured
  selector was introduced;
- the canonical workbook, source solver data and the active STU005 GPU run
  were not changed or interrupted. GitHub Actions were not used.

Historical note: this five-class experiment was later rejected. Its analyzer
was removed; `analysis/human-5` remains only as archived audit evidence and is
not an active workflow or source of truth.


## 2026-09-15 — strict five-class STU002 BB response revision

Status: STARTED

Base commit: `0f3c903` (local only; `main` is one commit ahead of
`origin/main`).

Scope: replace the rejected five-column candidate with a genuinely simple
version for `03_BB_AFTER_CBET`: exactly five visible flop classes, pure
F/C/R or exact 50/50 C/R cells, and no cell-specific hidden C/F selectors.
The existing global BDFD action may remain only where the split is material.

Plan: clean the interrupted partial edit, regenerate all audits from tracked
combo/action EV, review frequency/composition and EV tails with GPT-6 Astra,
document the result, validate, amend the unpushed commit, and request explicit
authorization before pushing. The active STU005 GPU run remains untouched.

Status: SUPERSEDED

The strict five-class intermediate candidate was not promoted. The later
user-approved four-class revision replaces it and is recorded below; its audit
is regenerated from the same tracked combo data.


## 2026-09-15 — resilient batch summaries during STU005 resume

Status: STARTED

Base commit: `0f3c9038b8a047ed8d53251b1998ac880e737d62` (local; `origin/main` is `2738ee92d40bd02690b77e413fd7dd9042e7b2a9`).

Observed failure: all four missing `01_BB_FIRST` boards were solved, but the six-branch runner stopped before branch 2 because `batch-summary.json` was held open by the Local Desktop Commander Node process. The raw branch has 286/286 complete board artifacts; no solver process remains active.

Scope: make summary publication resilient to a reader locking the optional raw JSON, validate resume against the completed first branch, then continue the existing STU005 run. Preserve every solver output and all unrelated human-table work. GitHub Actions are out of scope.

Plan: make CSV the canonical resume/parsing summary and publish it first; treat an `IOException` writing raw JSON as non-fatal and save a timestamped fallback; regenerate the compact dataset JSON from the canonical CSV; parse all PowerShell files, exercise the locked-file resume path without re-solving completed boards, then launch `run-all.ps1 -Resume` and verify branch 2 reaches a live GPU solve.

Status: COMPLETED

Implementation and validation:

- `tsgpu-batch.ps1` now publishes canonical `batch-summary.csv` before JSON and converts a locked raw JSON write into a timestamped fallback plus warning;
- `run-flop-study-branch.ps1` parses the canonical CSV, restores numeric/null types, and creates the compact dataset JSON independently of the raw JSON lock;
- all PowerShell files parsed successfully and `git diff --check` passed;
- the four completed-but-unpublished `01_BB_FIRST` rows were recovered from their validated `run.json`/`combos.json` artifacts without another GPU solve;
- the live locked-file test passed: `01_BB_FIRST` completed 286/286, fallback JSON was written, the compact dataset was built, and `run-all.ps1 -Resume` advanced to `02_BTN_AFTER_CHECK`;
- the second branch produced its first two successful boards and a live TexasSolverGPU child process was verified.

Remaining operational note: a reader may continue holding the old raw `batch-summary.json`; this no longer blocks solving, resume, parsing or compact dataset publication.


## 2026-09-15 - document and reproduce the final BB defense simplification

Status: STARTED

Base commit: `349c9efb9043403997a5d26059420728bf42a832` (local `main`; `origin/main` is `2738ee92d40bd02690b77e413fd7dd9042e7b2a9`).

Scope: record how the primary analysis and GPT-6 Astra review produced the simplified `STU002 / 03_BB_AFTER_CBET` teaching table, then record the user-approved principles for human bluff check-raises, deterministic CALL/FOLD selection and numeric acceptance limits. Make the exact four-column `ABB / BBB`, `Axx`, `Bxx`, `[9-2]xx` result reproducible from tracked combo data.

Constraints: preserve the canonical ten-column workbook and every solver/source artifact; do not disturb the active STU005 GPU solve; do not use GitHub Actions; keep unrelated generated STU005 files out of Git.

Plan:

1. update the methodology with the chronological primary-analysis/Astra/local-reproduction protocol;
2. document the revised check-raise composition principle and agreed frequency/EV/tail guardrails;
3. remove the branch-specific human analyzer and keep the old `human-5` evidence only as an explicitly rejected historical audit;
4. verify that the universal generator remains unchanged and has no human-table input or output;
5. close this log entry, inspect the staged diff, commit and push `main`.


Status: COMPLETED

Result:

- documented the manual analyst -> Astra critique -> local verification -> user approval workflow;
- recorded the final four-class `03_BB_AFTER_CBET` table, branch-only check-raise principles, numeric guardrails and reproduced audit metrics;
- removed `scripts/analyze-human-bb-response.py`; no supported script generates, consumes or promotes a human table;
- retained `analysis/human-5` only as the explicitly rejected historical five-class audit;
- verified that `generate-flop-strategies.py`, `flop_strategy.py` and `flop_workbook.py` are unchanged from `origin/main`;
- `git diff --check`, Python compilation of the universal generator modules and parsing of every PowerShell script passed;
- runner PID 4488 and TexasSolverGPU PID 25852 remained alive; active untracked STU005 output was not staged or modified;
- GitHub Actions were not used.


## 2026-09-15 — simplify STU002 UTG response to BB check-raise

Status: STARTED

Base commit: `b37648ec946d922013d86b0e42cf35d1adb3ee1d` (`main` synchronized with `origin/main`).

Scope: manually simplify only `STU002 / 04_UTG_AFTER_CHECK_RAISE`, where UTG chooses FOLD or CALL after `BB CHECK -> UTG BET 1/2 -> BB CHECK-RAISE 60`.

Constraints: use the tracked solver combo/EV export; do not run GPU solver; do not change or add a human-table generator; preserve the canonical workbook and active untracked STU005 solve; do not use GitHub Actions.

Plan: audit the existing seven-column table, test the smallest familiar exhaustive flop partitions and observable row-wide CALL/FOLD boundaries, measure total continuation and EV tails, obtain an independent GPT-6 Astra critique, reproduce accepted suggestions locally, present alternatives for user approval, then document, commit and push only after approval.


Status: AWAITING USER APPROVAL

Analysis checkpoint:

- audited 75,236 positive-reach combo rows from the tracked branch export; GPU solver was not run;
- corrected a temporary overbroad `ABB` test before approval; exact board counts are ABB 6, Axx 60, BBB 4, Bxx 160 and low 56;
- the recommended manual candidate has three columns: `ABB / BBB`, `Axx / Bxx`, `[9-2]xx`;
- candidate FOLD/CALL is 37.1501/62.8499% versus solver 39.2341/60.7659%, a +2.0840 pp CALL deviation;
- mean source loss is 0.156224 bb locally and 0.010637 bb after the documented node-reach scaling; clipped loss is 0.168665 bb locally and 0.011484 bb at root;
- P95/P99 local oracle regret is 0.560665/5.015470 bb; 5.2160%/3.8886% reach exceeds 0.5/1.0 bb;
- keeping five columns and a separate `Second pair / Axx = SUITED` rule saves only about 0.000345 bb at root;
- independent GPT-6 Astra review selected the same three-column candidate and identified the tiny deliberate Top-pair/BBB BDFD overcall as the cost of merging ABB with BBB;
- no human generator or generated human artifact was created; the production workbook and active STU005 output remain untouched.


Status: COMPLETED

Approval and publication:

- the user explicitly approved the three-column candidate;
- added `docs/UTG_CHECK_RAISE_RESPONSE_SIMPLIFICATION.md` with the exact table, definitions, metrics and accepted distortions;
- linked the worked example from `README.md`, `AGENTS.md`, `HISTORY.md` and `BATCHER_EVOLUTION.md`;
- kept the universal generator, canonical solver-frequency workbook and solver data unchanged;
- validated locally only; GitHub Actions were not used;
- active STU005 solver output remains untracked and excluded from this change.


## 2026-09-15 — simplify STU002 UTG response to BB donk

Status: STARTED

Base commit: `98466cd2cfdce1eff5bb4c6b80d143a03308c53a` (`main` synchronized with `origin/main`).

Scope: manually simplify only `STU002 / 05_UTG_AFTER_DONK`, where UTG chooses FOLD, CALL or native-60 RAISE after `BB DONK 1/2`.

Constraints: use the tracked solver combo/action-EV export; do not run GPU solver; do not change or add a human-table generator; preserve the canonical workbook and active untracked STU005 solve; do not use GitHub Actions.

Plan: audit the current five-column table, test smaller familiar exhaustive flop partitions, preserve a learnable value-plus-direct-draw raise range, reject hidden cell-specific selectors, measure total F/C/R, hand-row and board-family skew plus EV tails, obtain an independent GPT-6 Astra critique, and present the locally reproduced candidate for user approval before final documentation.


Status: COMPLETED

Approval and publication:

- the user explicitly approved the three-column candidate;
- added `docs/UTG_DONK_RESPONSE_SIMPLIFICATION.md` with the exact table, source provenance, metrics, Astra review and accepted distortions;
- linked the worked example from `README.md`, `AGENTS.md`, `HISTORY.md`, `HUMAN_STRATEGY_SIMPLIFICATION.md` and `BATCHER_EVOLUTION.md`;
- kept the universal generator, canonical solver-frequency workbook and solver data unchanged;
- no human-table generator or generated human workbook was added;
- active untracked STU005 solver output remains excluded from this change;
- GitHub Actions were not used.


## 2026-09-15 - simplify STU002 BB response to UTG donk-raise

Status: STARTED

Base commit: `483fbbcfd146ed26e5d821c6487154d9c2c116fc` (`main` synchronized with `origin/main`).

Scope: manually simplify only `STU002 / 06_BB_AFTER_DONK_RAISE`, where BB chooses FOLD or CALL after `BB DONK 1/2 -> UTG RAISE 60`.

Constraints: use the tracked solver combo/action-EV export; do not run GPU solver; do not add or change a human-table generator; preserve the canonical workbook and active untracked STU005 solve; do not use GitHub Actions.

Branch-specific direction: because this is a rare deep branch, test a stronger value-oriented simplification and accept more frequency deviation when the fixed-opponent root EV audit remains within an explicitly reported limit. Prefer pure CALL/FOLD; retain `BDFD`, `Ax` or `PAIR` only when raw combo data proves that the observable selector prevents a material error.

Plan: audit the five-column table, test the familiar three-class partition `ABB / BBB`, `Axx / Bxx`, `[9-2]xx`, compare value-heavy pure policies with the old conditional policy, report total continuation and hand/flop subgroup skew plus EV tails, obtain an independent GPT-6 Astra critique, then present the locally reproduced candidate for user approval before final documentation.


Status: COMPLETED

Approval and publication:

- the user approved the three-column value-and-draw candidate and the separate rare deep-branch simplification principle;
- added `docs/BB_DONK_RAISE_RESPONSE_SIMPLIFICATION.md` with the exact table, selector evidence, metrics, tail cost and Astra review;
- linked the approved example from `README.md`, `AGENTS.md`, `HISTORY.md`, `HUMAN_STRATEGY_SIMPLIFICATION.md` and `BATCHER_EVOLUTION.md`;
- recorded the owner's standing instruction to push each completed task in this repository to `PromSoftService/solver` `main`;
- kept all production generators, canonical workbooks and solver/source data unchanged;
- active untracked STU005 solver output remains excluded from the commit;
- GitHub Actions were not used.


## 2026-09-15 - simplify STU004 UTG response to BTN stab

Status: STARTED

Base commit: `e24149d5be0044964fae187c0a5a1a9a977b4bbb` (`main` synchronized with `origin/main`).

Scope: manually simplify only `STU004 / 04_UTG_AFTER_STAB`, where UTG chooses FOLD, CALL or RAISE after `UTG CHECK -> BTN STAB 1/2`.

Constraints: use the tracked solver combo/action-EV export; do not run GPU solver; do not add or change a human-table generator; preserve the canonical workbook and active untracked STU005 solve; do not use GitHub Actions.

Plan: audit the current five-column table; test the exhaustive three-class partition `ABB / BBB`, `Axx / Bxx`, `[9-2]xx` and only the smallest necessary expansions; preserve a learnable value-plus-direct-draw raise range; measure total F/C/R, hand-row and flop-family skew, selectors and EV tails; obtain independent GPT-6 Astra critique; present the locally reproduced candidate for approval before final documentation.


Status: COMPLETED

Approval and publication:

- moving to the next branch confirmed the four-column candidate;
- added `docs/UTG_STAB_RESPONSE_SIMPLIFICATION.md` with the exact table,
  rejected three-class merge, metrics, tail comparison and Astra review;
- linked the approved example from `README.md`, `AGENTS.md`, `HISTORY.md`,
  `HUMAN_STRATEGY_SIMPLIFICATION.md` and `BATCHER_EVOLUTION.md`;
- kept every production generator, canonical workbook and solver/source
  artifact unchanged;
- active untracked STU005 output remains excluded;
- GitHub Actions were not used.


## 2026-09-15 - simplify STU004 BTN response to UTG c-bet

Status: STARTED

Base commit: `e0c7ff2` (`main` synchronized with `origin/main`).

Scope: manually simplify only `STU004 / 03_BTN_AFTER_CBET`, where BTN
chooses FOLD, CALL or RAISE after UTG c-bets one half-pot.

Constraints: use the tracked solver combo/action-EV export; do not run the GPU
solver; do not add or change a human-table generator; preserve the canonical
workbook and active untracked STU005 output; do not use GitHub Actions.

Plan: audit the current five-column table; test the smallest exhaustive familiar
partitions, beginning with `ABB / BBB`, non-paired `Axx`, non-paired `Bxx`
and `[9-2]xx`; preserve a learnable value-plus-direct-draw raise range;
measure total F/C/R, row/flop composition and EV tails; obtain independent
GPT-6 Astra review; present a reproduced candidate for approval before final
documentation.


Status: COMPLETED

Approval and publication:

- the user's consolidated strategy block confirmed the three-column candidate;
- added `docs/BTN_CBET_RESPONSE_SIMPLIFICATION.md` with the exact table,
  deterministic Weak-pair boundary, metrics and accepted distortions;
- synchronized the approved BB-defense display by merging identical Axx and
  Bxx action vectors; this presentation-only merge changes no policy or metric;
- linked both approved teaching artifacts from the repository documentation;
- kept all generators, canonical workbooks and solver/source data unchanged;
- validated locally only; GitHub Actions were not used;
- active untracked STU005 solver output remains excluded.


## 2026-09-15 - audit STU002 UTG c-bet initiative table

Status: STARTED

Base commit: `f7216e6bc1492573ec4c134e5fd66b69264b8187` (`main` synchronized with `origin/main`).

Scope: manually re-audit only `STU002 / 02_UTG_AFTER_CHECK`, where UTG chooses CHECK or BET 1/2 after BB checks.

Constraints: use the tracked combo/action-EV export; do not run the GPU solver; do not change the generator or canonical workbook; preserve active STU005; do not use GitHub Actions.

Plan: reproduce the current three-column table frequencies; test allowed `X`, `B15/X85`, `B/X` and `B` policies and the smallest familiar exhaustive flop partitions; audit total BET, hand-category and board-family composition, local/root EV and loss tails; obtain an independent GPT-6 Astra critique; reproduce accepted suggestions locally; present the candidate for approval before updating teaching documents or trainer.


Status: COMPLETED

Approval and publication:

- the user approved the four-class `A-high / K/Q-high / J/T-high / 9-high and lower` table;
- recorded the exact table, metrics, deliberate row distortions and rejected B15 experiments in `docs/UTG_CBET_VS_BB_SIMPLIFICATION.md`;
- GPT-6 Astra independently reviewed the evidence; every accepted or rejected suggestion was reproduced from tracked combo data;
- kept the generator, canonical workbook, trainer and active STU005 output unchanged;
- validated locally only; GitHub Actions were not used.


## 2026-09-15 - audit STU004 UTG c-bet initiative table

Status: STARTED

Base commit: `d7f3204` (`main` synchronized with `origin/main`).

Scope: manually re-audit only `STU004 / 01_UTG_FIRST`, where UTG chooses CHECK or BET 1/2 against BTN.

Constraints: use the tracked combo/action-EV export; do not run the GPU solver; do not change the generator, canonical workbook or trainer; preserve active STU005; do not use GitHub Actions.

Plan: reproduce the approved three-column teaching table; search the smallest familiar exhaustive flop classes; test `X`, `B15/X85`, `B/X` and `B`; audit total BET, BET-range composition, local/root EV and tails; obtain an independent GPT-6 Astra critique; present one reproduced candidate for approval before documentation changes.


Status: COMPLETED

Approval and publication:

- the user approved the original three flop classes with pure BET for Two pair+ and Overpair on `AKx / Kxx`;
- recorded the exact table, metrics, classifier priority and accepted completed-straight exception in `docs/UTG_CBET_VS_BTN_SIMPLIFICATION.md`;
- GPT-6 Astra independently reviewed the evidence and the accepted claims were reproduced from tracked combo data;
- kept the generator, canonical workbook, trainer and active STU005 output unchanged;
- validated locally only; GitHub Actions were not used.


## 2026-09-15 - audit STU004 BTN stab initiative table

Status: STARTED

Base commit: `2283771` (`main` synchronized with `origin/main`).

Scope: manually re-audit only `STU004 / 02_BTN_AFTER_CHECK`, where BTN chooses CHECK or BET 1/2 after UTG checks.

Constraints: use the tracked combo/action-EV export; do not run the GPU solver; do not change the generator, canonical workbook or trainer; preserve active STU005; do not use GitHub Actions.

Plan: reproduce the approved three-column teaching table; test the smallest familiar exhaustive flop classes and `X`, `B15/X85`, `B/X`, `B`; audit total BET, hand-row and board-family composition, root EV and tails; obtain independent GPT-6 Astra review; present one locally reproduced candidate before documentation changes.


Status: COMPLETED

Approval and publication:

- the user approved pure BET for Two pair+ on K/Q-high and Gutshot on A-high while retaining the three existing flop classes;
- recorded the exact table, metrics, classifier priority and accepted row/tail exceptions in `docs/BTN_STAB_VS_UTG_SIMPLIFICATION.md`;
- GPT-6 Astra independently reviewed the evidence and all accepted claims were reproduced from tracked combo data;
- kept the generator, canonical workbook, trainer and active STU005 output unchanged;
- validated locally only; GitHub Actions were not used.


## 2026-09-15 - audit STU002 BB donk initiative table

Status: STARTED

Base commit: `0679731` (`main` synchronized with `origin/main`).

Scope: manually re-audit only `STU002 / 01_BB_FIRST`, where BB chooses CHECK or DONK BET 1/2.

Constraints: use the tracked combo/action-EV export; do not run or interrupt the GPU solver; do not change the generator, canonical workbook or trainer; preserve active STU005; do not use GitHub Actions.

Plan: reproduce the current rule that donks only `[7-4]x`; test the smallest familiar exhaustive board partition and `X`, `D15/X85`, `D/X`, `D`; audit total DONK, hand-row and board-family composition, root EV and tails; obtain independent GPT-6 Astra review; present one locally reproduced candidate before documentation changes.

Status: COMPLETED

Approval and publication:

- the user approved the two-class `[9-8]xx / [7-4]xx` table, with T-high and higher boards always CHECK;
- recorded the exact table, metrics, rejected one-column alternative and GPT-6 Astra revision in `docs/BB_DONK_SIMPLIFICATION.md`;
- kept the generator, canonical workbook, trainer and active STU005 output unchanged;
- validated locally only; GitHub Actions were not used.


## 2026-09-16 - synchronize standalone flop trainer with approved tables

Status: STARTED

Base commit: `5171893` (`main` synchronized with `origin/main`).

Scope: update the standalone mobile HTML trainer to the ten approved STU002/STU004 teaching tables and their full explanations.

Constraints: do not add the standalone trainer to the solver repository; do not change solver/generator/workbook code; do not touch or interrupt active STU005; do not use GitHub Actions.

Plan: update branch data, mutually exclusive flop classifiers and explanations; prevent impossible BB-donk histories outside the approved low-board classes; validate all ten selectable branches, table dimensions, actions, random deals and mobile HTML locally; publish the updated standalone HTML, then close this work-log entry.

Status: COMPLETED

Result:

- updated the existing standalone `poker_flop_strategy_trainer.html` to all ten approved STU002/STU004 teaching tables and full explanations;
- added the approved two-class BB-donk strategy, four-class UTG-vs-BB c-bet strategy and all approved simplified response tables;
- updated path filtering so `D15/X85` is a valid rare donk while BB-donk and donk-raise branches remain impossible on T-high and higher boards;
- preserved the ten-branch checkbox filter, side-by-side weighted ranges, soft action colours and mobile portrait layout;
- validated JavaScript syntax, HTML parsing, 12 hand rows per table, all table dimensions, all 286 board-rank classifications, 25 generated questions per branch and full explanation rendering;
- confirmed 36 `[9-8]xx` boards, 20 `[7-4]xx` boards and 230 T-high+ boards excluded from donk generation;
- standalone file SHA-256: `63f42c613051c61e57deabcc3a901c89b168bf912c8b52bdbe7be777228c02b2`;
- solver, generator, canonical workbooks and active STU005 output were unchanged; GitHub Actions were not used.

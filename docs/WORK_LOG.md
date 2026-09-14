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

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

# Universal strategy progress

## Current instruction — overrides the historical review
The user corrected the method: **EXP-003 is REJECTED AS FINAL COMPRESSION METHOD.** Preserve its scripts/results as a negative experiment. Do not rerun EXP-001/002/003. CANCEL the proposed BTN_DEF33 Air -> FOLD whole-row experiment.

The unit of analysis is flop class x hand class IN EACH SPOT. Common axes do not require common actions, across either board classes or spots. The boundary/MIX objective encouraged premature compression and allowed structurally poor strategies within aggregate budgets.

## Current stage: EXP-004 RAW CELL STRUCTURE
Seven independent solver-profile matrices; unchanged operational 13-class grid from core.py; fixed 15 hand rows. NO human action selection, whole-row replacement, smoothing, optimization, category merging or user Markdown replacement in this stage.
Planned isolated script: tools/raw_cell_structure.py. Isolated workflow: .github/workflows/raw-cell-structure.yml. Do not modify or dispatch universal-strategy-analysis.yml, because it reruns old experiments. New script deliberately lives outside its tools/universal_strategy/** trigger.

## Source checkpoint and historical review
Resumed from main 372cc544d708e4776b39a902d6eb38ebabf4827a. Read current AGENTS.md, README.md, docs/STUDY_REGISTRY.md, PROGRESS.md, core.py and existing workflow.
Full preceding manual review remains in Git at `372cc544d708e4776b39a902d6eb38ebabf4827a:analysis/universal_strategy/PROGRESS.md`, blob 137aa1c5252c93c47facab02e8aae9302195e3f0. Its old Next step is CANCELLED. All prior experiment artifacts remain untouched.
A Git object-only archive commit d7f8348dcdbbe90488cf7d95aae65104e7185860 was prepared but not used to move main; use main as source of truth, not that object.

## Goal
Learnable solver-like flop strategy with common axes and independent cells, without expensive mistakes. Personal preflop and reference/theory in strategy_structured.md must be preserved and must never be solver inputs.

## Fixed constraints
- Registered RNG001 / RNG002 datasets and their CFG/NOD only; keep fractional weights. Personal Markdown ranges excluded.
- BRD001 only, 286 unpaired rainbow flops; do not generalize to all NL2.
- Up to 13 mutually exclusive, exhaustive, readable flop classes; no opaque names. Begin detailed; only later consider evidence-based merges.
- Fixed 15 hand rows. Any pair is shorthand, never another row.
- Normalize reach_probability within each study, not pooled raw reach across nodes. Show cell-conditional frequencies/losses, cell share of class and study, and distinguish absent cells from zero-reach cells.
- Equity forbidden. No BR/strategy lock. loss_if_action = best pure EV - action EV; extra loss versus exported mixed is distinct.
- No runners/configs/ranges/datasets changes. One user turn = one logical stage; show progress and STOP after checkpoint.

## Datasets
Under datasets/:
1. DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv — UTG_BB_BET, IP B33 c-bet X/B.
2. DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv — BB_DEF33, F/C/R, implicit NOD001.
3. DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv — BB_DEF75, F/C/R, implicit NOD001.
4. DS__RNG002__CFG003__NOD003__BRD001__RUN-20260907-115423.csv — UTG_BTN_BET, OOP X/B.
5. DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv — BTN_DEF33, F/C/R.
6. DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv — BTN_STAB, X/B after UTG check.
7. DS__RNG002__CFG003__NOD006__BRD001__RUN-20260907-192002.csv — UTG_DEF33, F/C/R after UTG check / BTN B33.

## Current flop classification
Unchanged core.board_class(grid='thirteen'). B=K/Q/J/T; sorted high>middle>low. con means the TWO LOWER ranks are consecutive, not generic connectivity. BBx includes connected boards; not identical to old BBx dis examples.

| Class | Exclusive definition |
|---|---|
| ABB | high A, low >=T |
| A[K/Q]x | high A, middle K/Q, low <=9 |
| A[J-T][9-5] | high A, middle J/T, low 5..9 |
| A[J-T][4-2] | high A, middle J/T, low 2..4 |
| A[9-7]x | high A, middle 7..9 |
| A[6-2]x | high A, middle <=6 |
| BBB | no A, all three ranks >=T |
| BBx | no A, middle >=T, low <=9 |
| K/Qx dis | high K/Q, middle <=9, middle-low !=1 |
| K/Qx con | high K/Q, middle <=9, middle-low =1 |
| [J-8]x dis | high J..8, middle <=9, middle-low !=1 |
| [J-8]x con | high J..8, middle <=9, middle-low =1 |
| [7-4]x | high 7..4 |

## Current hand order and semantics
Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair | Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing.
Unchanged core.py v2: made first; Underpair strictly between top and middle, Weak pair below middle. Bare A-high without direct straight draw or BDFD remains A-high even with BDSD. Otherwise 2OC+direct straight draw/BDFD/BDSD precedes Combo draw. Combo draw means direct straight draw + BDFD on rainbow. OESD includes double gutshots. Any pair covers the six single-pair rows only. Display is fixed, but broad buckets do not give an exact universal clean-outs/strength ranking; do not hide that limitation.

## Experiments completed
- EXP-001 input audit: GHA 34160422762, code a0fb378588501718aefecfbcd49785d6aa0fad92. experiments/EXP-001.json/.md. KEEP audit, no rerun.
- EXP-002 architecture comparison: GHA 34160712982, code dc66bcb055d26dd68572d91e08458a6a430fe379. experiments/EXP-002.json/.md, maps/. KEEP results; screening failure not universal impossibility. No rerun.
- EXP-003 fixed-grid candidates: same GHA/code, experiments/EXP-003.json/.md, maps/. REJECTED AS FINAL COMPRESSION METHOD. Six maps / ten MIX is historical only. Preserve numeric results and manual review, no rerun.

## Current best candidate
None accepted. EXP-004 describes solver profiles only. Seven separate decision problems on common axes, not a preset target number of policies.

## Rejected ideas
Premature sharing of actions; choosing six columns merely for fewer boundaries; mandatory whole-row actions; approving composition distortion from overall means; confusing local loss with adaptive exploitability.

## Next step
Run ONLY EXP-004 on the unchanged detailed grid. Save per-study profiles, complete JSON/CSV/Markdown, actual GHA run provenance and descriptive neighboring-column similarities. Inspect logs and matrices; record natural regions and provisional merge suggestions. Do not choose human actions or perform merges. STOP after this one stage.

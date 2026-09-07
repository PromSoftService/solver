# Universal strategy progress

## Goal
Learnable solver-like flop strategy with common flop/hand axes and independent cells, without expensive mistakes. Personal preflop and reference/theory in strategy_structured.md must be preserved and must never become solver inputs.

## Status — EXP-004 completed; STOP
Completed one stage: RAW CELL STRUCTURE for all seven independent spots on the detailed 13 x 15 grid. No human actions selected, no row-wide edits, no smoothing, no policy search, no category or action-map mergers. strategy_structured.md is unchanged.
Script: `tools/raw_cell_structure.py`. Isolated workflow: `.github/workflows/raw-cell-structure.yml`.
GHA `34163552623`, job `101870061605`, source code `3c88ccb90818882716a5734644fcce6afb3ce1b5`; computed results checkpoint `c370746`. Actual job logs inspected: all seven profiles generated, protected files unchanged, Markdown table syntax valid. Downloaded artifact `10033402931` verified by SHA-256 `5fb46f573a98509d5819adde94e03016c67add92136331d56ecda1b34dde9683`.
Descriptive findings saved as `experiments/EXP-004-findings.md`, commit `7548162c3b9a3ee69b2ab57c1c3b4bfb6b4cab1b`.
Do not dispatch the old universal-strategy-analysis.yml: it reruns EXP-002/003. No old experiment was rerun in this stage.

## Method correction — overrides historical instructions
**EXP-003: REJECTED AS FINAL COMPRESSION METHOD.** Keep its scripts/results as a negative experiment. Its boundary/MIX objective encouraged premature compression and allowed structurally poor policies within aggregate budgets.
The unit is flop class x hand class IN EACH SPOT. Common axes do not require common actions across either board classes or spots. CANCEL the old BTN_DEF33 Air -> FOLD whole-row experiment. This is not a ban on identical actions where the data justify them; it is a ban on requiring whole rows to be uniform.
Original detailed manual review remains in Git at `372cc544d708e4776b39a902d6eb38ebabf4827a:analysis/universal_strategy/PROGRESS.md`, blob `137aa1c5252c93c47facab02e8aae9302195e3f0`. That historical Next step is cancelled. All old experiment artifacts remain unchanged.

## Fixed constraints
- Registered RNG001 / RNG002 datasets and their CFG/NOD only. Keep fractional weights; exclude personal Markdown ranges.
- BRD001 only, 286 unpaired rainbow flops. Do not generalize to all NL2.
- At most 13 mutually exclusive, exhaustive, human-readable flop classes. Detailed initial grid, then evidence-based merges only.
- Fixed 15 hand rows and display order. Any pair is shorthand, not another row.
- Normalize reach_probability within each study; never pool unnormalized weights across nodes. Report cell-conditional frequencies/losses and cell shares of class/study. Distinguish absent cells and zero reach.
- Equity forbidden. No BR/strategy-lock. loss_if_action = best pure EV - action EV; extra loss vs exported mixed is distinct.
- Simplicity before tiny EV gains; preserve meaningful range composition and error tails. Do not force monotonicity or rectangles against the profiles.
- No runners/configs/ranges/datasets changes. One user turn = one logical stage, visible updates, checkpoint then STOP.

## Datasets
Under datasets/:
1. DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv — UTG_BB_BET, IP B33 c-bet X/B.
2. DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv — BB_DEF33, F/C/R, implicit NOD001.
3. DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv — BB_DEF75, F/C/R, implicit NOD001.
4. DS__RNG002__CFG003__NOD003__BRD001__RUN-20260907-115423.csv — UTG_BTN_BET, OOP X/B.
5. DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv — BTN_DEF33, F/C/R.
6. DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv — BTN_STAB, X/B after UTG check.
7. DS__RNG002__CFG003__NOD006__BRD001__RUN-20260907-192002.csv — UTG_DEF33, F/C/R after UTG check / BTN B33.

## Current architecture
Seven independent solver-profile matrices on common axes. Human action maps and final map count NOT selected. Do not turn a shared layout into a shared-action constraint.

## Current flop classification
Unchanged core.board_class(grid='thirteen'), core Git blob `18a139a74aeb0eebf7df6b92033986440af146e7`. B=K/Q/J/T; high>middle>low. con means the TWO LOWER ranks are consecutive; BBx includes connected boards. This is the recorded operational grid, not an exact reconstruction of historical BBx dis examples.

| Class | Exclusive definition | Boards |
|---|---|---:|
| ABB | high A, low >=T | 6 |
| A[K/Q]x | high A, middle K/Q, low <=9 | 16 |
| A[J-T][9-5] | high A, middle J/T, low 5..9 | 10 |
| A[J-T][4-2] | high A, middle J/T, low 2..4 | 6 |
| A[9-7]x | high A, middle 7..9 | 18 |
| A[6-2]x | high A, middle <=6 | 10 |
| BBB | no A, all three ranks >=T | 4 |
| BBx | no A, middle >=T, low <=9 | 48 |
| K/Qx dis | high K/Q, middle <=9, middle-low !=1 | 42 |
| K/Qx con | high K/Q, middle <=9, middle-low =1 | 14 |
| [J-8]x dis | high J..8, middle <=9, middle-low !=1 | 67 |
| [J-8]x con | high J..8, middle <=9, middle-low =1 | 25 |
| [7-4]x | high 7..4 | 20 |

## Current hand order and semantics
Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair | Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing.
Unchanged core.py v2: made first; Underpair strictly between top and middle; Weak pair below middle. Bare A-high without direct straight draw/BDFD remains A-high even with BDSD. Otherwise 2OC+direct straight draw/BDFD/BDSD precedes Combo draw. Combo draw = direct straight draw + BDFD on rainbow. OESD includes double gutshots. Any pair covers six single-pair rows only. Broad categories do NOT give an exact universal clean-outs/strength order; do not hide this limitation or silently reinterpret rows. These semantics were not changed in EXP-004.

## Experiments completed
- EXP-001 input audit: GHA 34160422762, code a0fb378588501718aefecfbcd49785d6aa0fad92; experiments/EXP-001.json/.md. KEEP audit, no rerun.
- EXP-002 architecture comparison: GHA 34160712982, code dc66bcb055d26dd68572d91e08458a6a430fe379; experiments/EXP-002.json/.md and maps/. KEEP numerical results, screening failure not universal impossibility. No rerun.
- EXP-003 fixed-grid candidates: same GHA/code; experiments/EXP-003.json/.md and maps/. REJECTED AS FINAL COMPRESSION METHOD, preserve as negative experiment. Historical six maps/ten MIX is not an approved policy. No rerun.
- EXP-004 raw profiles: GHA 34163552623. KEEP DESCRIPTIVE BASELINE ONLY. 1365 cells, full per-action frequencies/reach/EV/loss/tails. No actions or merges chosen.

## EXP-004 outputs
- experiments/EXP-004-matrices.md — seven compact numeric matrices, same 15 rows and 13 columns; class reach/frequencies.
- experiments/EXP-004.md — full frequency/reach/forced-action loss matrices; descriptive neighbor distances.
- experiments/EXP-004.json — full precision, profiles, loss quantiles/tails and neighbor diagnostics.
- experiments/EXP-004-cells.csv — flattened cells.
- experiments/EXP-004/*.json — per-study checkpoints.
- experiments/EXP-004-findings.md — observations, exact supporting examples and provisional merge ideas.

## Observations and candidate mergers — not implemented
- UTG c-bet vs BB: multiple A-high rows reduce betting together, while Two pair+ and direct draws remain active longer. Do not impose strict ready-hand monotonicity: Second pair can bet more than Top pair.
- BB defense B75: low pair/backdoor/Air fold region is visible; the medium-pair boundary changes across boards.
- UTG defense after check: on K/Q and lower boards raises expand in several value/draw rows, not one row only.
- First provisional merge candidate: [J-8]x dis/con. Mean same-hand profile TV across seven studies ranges 1.7..8.2pp. Caveats: BB_DEF33 Weak pair CALL 95.2/74.7%; UTG_BB_BET Weak pair BET 43.9/9.5%. Forced-action loss and reach for these cells are disclosed in findings. No merge cost calculated.
- K/Qx dis/con is less clear: UTG_BB_BET mean profile gap 13.1pp; several defense draw/weak-pair rows differ 20+pp.
- Two A[J-T] columns are conditional candidates, but UTG_DEF33 Weak pair FOLD 54.9/28.0% and BB_DEF75 Combo draw FOLD 26.2/~0% require attention.
- Keep A[9-7]x vs A[6-2]x distinct for now: UTG_BB_BET profile gap 25.2pp and whole-range BET 56.8/29.6%. Similarity in the other six studies must not conceal this difference.
- Rare extreme profile cells must be weighted: BTN_DEF33 Air on [7-4]x RAISE 91.66% represents only 0.0003055% study reach. No human rule inferred from that number.

## Current best candidate
None accepted. Current result is a complete descriptive basis for later cell-based simplification, not a playing strategy.

## Next step
WAIT for a new user message. Then choose ONE bounded human-action or merge-evaluation step using the already saved EXP-004 cells. Do not recompute EXP-004 merely to recover context, do not rerun EXP-001/002/003, and do not resurrect the whole-row Air edit. Most promising provisional merge boundary is [J-8]x dis/con, but no merge is validated until an actual proposed cell-policy is evaluated as a package. STOP now after reporting the raw profiles and findings.

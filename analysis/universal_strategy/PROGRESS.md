# Universal strategy progress

## Goal
Compress the seven existing BRD001 flop studies into a learnable human strategy with shared axes, few rules, and measured losses. Do not reconstruct every solver mixture. Replace only the postflop strategy in the user's `strategy_structured.md`; preserve personal preflop ranges and reference/theory material.

## Status
2026-09-07: resumed from remote main `537a4e3dd8ebfe706ba31b25f8e168d9a9ed7831`. Read current AGENTS.md, README.md and docs/STUDY_REGISTRY.md. No earlier PROGRESS.md exists. The previous universal workflow performed an input audit; no reproducible universal candidate comparison was committed. Earlier chat/screenshot numbers are not accepted as verified experimental results.

## Fixed constraints
- Postflop inputs: registered RNG001 (UTG vs BB) and RNG002 (UTG vs BTN) datasets only. Never substitute personal Markdown ranges.
- BRD001 only: 286 unpaired rainbow rank triples. No inference to other board families, positions, stacks or bet sizes.
- At most 13 mutually exclusive, collectively exhaustive human-readable flop classes; no opaque cluster names.
- Approved hand vocabulary: Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair, Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing.
- Any pair is a shorthand for the single-pair rows, not an additional row; Two pair+ is separate.
- Ready hands first, draws/high cards second; one fixed row order across all tables. Explicit definitions/precedence are required where labels overlap. Out counts are not equity or guaranteed clean winning outs.
- Start with pure actions; introduce 50/50 or 75/25 only when necessary. State the two actions in every mix. 80/90 only if justified by a reduction in rules.
- Simplicity and understandable action regions take priority over tiny EV improvements. No new hand rows for a 0.001bb improvement.
- Monitor local regret, action frequencies, hand-group composition and costly error tails; all weighted by reach_probability. Do not conceal opposing errors behind an overall average.
- Equity forbidden. No BR/strategy-lock/re-solve has been performed; local evaluations are not adaptive exploitability.
- Do not change runners, native configs, registered ranges or datasets for this analysis.
- Important results must be in committed scripts + machine-readable reports + this handoff, not just chat or Actions logs.

## Datasets
All filenames are under `datasets/`:
1. `DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv` — UTG IP c-bet B33 vs BB (X/B).
2. `DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv` — BB defense vs UTG B33 (F/C/R); implicit NOD001.
3. `DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv` — BB defense vs UTG B75 (F/C/R); implicit NOD001.
4. `DS__RNG002__CFG003__NOD003__BRD001__RUN-20260907-115423.csv` — UTG OOP c-bet B33 vs BTN (X/B).
5. `DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv` — BTN IP defense vs UTG B33 (F/C/R).
6. `DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv` — BTN IP stab B33 after UTG check (X/B).
7. `DS__RNG002__CFG003__NOD006__BRD001__RUN-20260907-192002.csv` — UTG OOP defense after check / BTN B33 (F/C/R).

## Current candidate architecture
Not selected. Compare the requested 2-template and 4-template architectures, and distinguish two meanings: a shared classification/layout with spot-specific cell actions versus literally sharing the same actions across spots. Shared axes do not require shared actions. Report both the number of axis systems and the number of actual action maps, so seven maps cannot be disguised as two strategies.

## Current flop classification
Not selected. Allowed starting templates: ABB; A[K/Q]x; BBB; BBx dis; K/Qx dis; A[J-T][9-5]; K/Qx con; A[9-7]x; [J-8]x dis; A[J-T][4-2]; [J-8]x con; [7-4]x; A[6-2]. Coarser allowed templates: A[K-J]x; A[T-2]x; BBx; K[9-2]x; [Q-8]x; [7-4]x. These are examples, not simultaneous overlapping classes. Exact con/dis and B definitions and full coverage must be tested before use. Do not assume the 13 prose templates are already an exhaustive partition.

## Current hand order
Use the approved order as the initial display order: Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair | Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing. Freeze one consistent order for every output. Definitions and classification precedence are pending validation; any clarification must be recorded explicitly, not silently inferred from old tables. In particular, broad pair/draw labels do not admit an exact universal ranking by showdown strength or clean outs.

## Experiments completed
### EXP-001 — dataset and taxonomy audit
Script: `tools/universal_strategy/audit.py`.
GHA run: 34160422762; code commit: a0fb378588501718aefecfbcd49785d6aa0fad92.
Results: `experiments/EXP-001.json` and `experiments/EXP-001.md`.
KEEP: all seven dataset hashes, schemas, coverage and EV identities pass.
Legacy 13-label examples cover only 127 boards. All 6/8/13 operational partitions cover 286.
The approved vocabulary is frozen; classifier definitions/precedence are documented in EXP-001.
No strategy architecture has yet been accepted.

### EXP-002 — verified bounded comparison

Script: `tools/universal_strategy/experiments.py --stage architectures`. GHA 34160712982, commit dc66bcb055d26dd68572d91e08458a6a430fe379. Reports: `experiments/EXP-002.json`, `.md`, `maps/`.

All 2/4 shared-action architectures were tested, plus alternative groupings. See report for actual statuses. One shared UTG BET policy has an unavoidable target-frequency error of at least 16.61pp in one spot. Shared taxonomy remains possible. No selected final candidate yet.

## Current best candidate
None. Do not overwrite the user's postflop document with an untested map.

## Rejected ideas
- Unbounded category search for tiny EV gains: rejected by user constraint, not by experiment.
- Treating a green optional-script workflow step as proof of a completed analysis: invalid.
- Assuming earlier screenshot-only comparisons are reproducible: invalid until rerun by committed code.

## Next step
Run EXP-003: fit individual maps, select the smallest feasible fixed grid and the simplest feasible cover of the seven studies. Review actual maps and tails before publishing.

# Universal strategy progress

## Goal
Compress the seven existing BRD001 flop studies into a learnable human strategy with shared axes, few rules, and measured losses. Do not reconstruct every solver mixture. Replace only the postflop strategy in the user's `strategy_structured.md`; preserve personal preflop ranges and reference/theory material.

## Status
Latest stage: manual/source review of EXP-003, resumed from remote main `56565d8e8e9a8ff6a77c0b24d76b3f80c97c787a`.
Read current AGENTS.md, README.md, docs/STUDY_REGISTRY.md, PROGRESS.md, saved EXP-001/002/003 reports, saved action maps, core.py and optimize.py. Inspected actual GHA job 101861829146 in run 34160712982: EXP-002 and EXP-003 ran successfully and were committed as f198124 and 56565d8.
NO solver, dataset aggregation, optimization or experiment rerun was performed in this review. No action map, dataset, runner, config, range or user strategy Markdown was changed.
Decision: KEEP the shared six-class taxonomy as a candidate; HOLD the automatic six-map package as an experimental baseline, but REJECT adopting it unchanged as the human strategy. Numeric screening passed, but manual review found expensive category-level errors and awkward rules. No final strategy has been approved.

Historical recovery: the first checkpoint resumed from 537a4e3 on 2026-09-07. That earlier workflow only audited inputs; screenshot-only universal strategy results were not accepted as reproducible experiments.

## Fixed constraints
- Postflop inputs: registered RNG001 (UTG vs BB) and RNG002 (UTG vs BTN) datasets only. Never substitute personal Markdown ranges.
- BRD001 only: 286 unpaired rainbow rank triples. No inference to other board families, positions, stacks or bet sizes.
- At most 13 mutually exclusive, collectively exhaustive human-readable flop classes; no opaque cluster names.
- Approved hand vocabulary: Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair, Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing.
- Any pair is a shorthand for the single-pair rows, not an additional row; Two pair+ is separate.
- Ready hands first, draws/high cards second; one fixed row order across all tables. Explicit definitions/precedence are required where labels overlap. Out counts are not equity or guaranteed clean winning outs.
- Start with pure actions; introduce 50/50 or 75/25 only when necessary. State both actions and their probabilities in every mix. 80/90 only if justified by a reduction in rules.
- Simplicity and understandable action regions take priority over tiny EV improvements. No new hand rows for a 0.001bb improvement.
- Monitor local regret, action frequencies, hand-group composition and costly error tails; all weighted by reach_probability. Do not conceal opposing errors behind an overall average.
- Equity forbidden. No BR/strategy-lock/re-solve has been performed; local evaluations are not adaptive exploitability.
- Do not change runners, native configs, registered ranges or datasets for this analysis.
- Important results must be in committed scripts + machine-readable reports + this handoff, not just chat or Actions logs.
- One user turn = one logical stage. Return to the user and STOP after the checkpoint. Do not start the Next step without a new user message.

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
One shared axis system, six ACTUAL action maps covering seven decisions. Only BB_DEF33 and UTG_DEF33 share actions. This is not two strategies disguised by a common layout.

| Map | Decisions covered | Saved MIX cells |
|---|---|---:|
| UTG_BB_BET | UTG IP c-bet B33 vs BB | 1 |
| BB_DEF33 + UTG_DEF33 | BB vs UTG B33; UTG after check vs BTN B33 | 9 |
| BB_DEF75 | BB vs UTG B75 | 0 |
| UTG_BTN_BET | UTG OOP c-bet B33 vs BTN | 0 |
| BTN_DEF33 | BTN vs UTG B33 | 0 |
| BTN_STAB | BTN B33 after UTG check | 0 |

Six maps are the saved bounded search choice, NOT a proof of the minimum human learning burden. Existing separate six-grid maps have BB_DEF33 = 0 mixed cells and UTG_DEF33 = 3 mixed cells. Therefore the shared map's nine MIX cells are not individually proven necessary. Keep this observation; do not rerun these existing maps to rediscover it.

## Current flop classification
EXP-003 candidate `six`, fixed column order:

| Class | Exact definition after sorting board ranks high > middle > low |
|---|---|
| A[K-J]x | high = A; middle = K, Q or J |
| A[T-2]x | high = A; middle <= T |
| BBx | no A; middle >= T (at least two ranks among K/Q/J/T, including three-Broadway boards) |
| K[9-2]x | high = K; middle <= 9 |
| [Q-8]x | high from Q through 8, after excluding BBx |
| [7-4]x | high from 7 through 4 |

Classification precedence is the table order, matching core.board_class(grid='six'). EXP-001 reports coverage of all 286 boards with no overlap. This review did not rerun coverage.
Allowed detailed templates remain available but no additional class is proposed in this stage. The historical 13 prose labels are examples, not a complete partition by themselves.

## Current hand order and semantics
Fixed DISPLAY order, unchanged:
Two pair+, Overpair, Top pair, Second pair, Third pair, Underpair, Weak pair | Combo draw, OESD, Gutshot, BDFD, 2 overcards + draw, 2 overcards, A-high, Air / Nothing.

Use core.py / EXP-003 definition v2, not the older EXP-001 precedence string where it differs:
1. Classify made hands first. Pocket above top = Overpair; pocket strictly between top and middle = Underpair; pocket below middle = Weak pair. A set is already Two pair+.
2. Bare A-high with no pair, direct straight draw or BDFD remains A-high even with a backdoor straight draw.
3. Otherwise two overcards plus direct straight draw, BDFD or BDSD = 2 overcards + draw. This classifier branch precedes Combo draw, although the display row is lower.
4. Remaining direct straight draw + BDFD = Combo draw; remaining two-completing-rank straight draw = OESD (includes double gutshot); remaining one-completing-rank straight draw = Gutshot; then BDFD, A-high, residual bare 2 overcards, Air / Nothing.
5. Any pair = the six single-pair rows only. It does not include Two pair+.

Semantic cautions: Underpair/Weak pair are not the old RNG002 broad Underpair/99- buckets. On rainbow Combo draw means straight draw + BACKDOOR flush draw, not a direct flush draw. Display order is consistent but is not a strict strength/outs ranking: e.g. a pocket between top and middle can beat second/third pair; 2OC+draw can contain a strong direct draw despite being displayed below BDFD. Do not silently claim this requirement is fully satisfied or reorder rows independently per spot. No definitions were changed during this review.

## Experiments completed
### EXP-001 — dataset and taxonomy audit
Script: `tools/universal_strategy/audit.py`.
GHA run: 34160422762; code commit: a0fb378588501718aefecfbcd49785d6aa0fad92.
Results: `experiments/EXP-001.json` and `experiments/EXP-001.md`.
KEEP: all seven dataset hashes, schemas, coverage and EV identities passed.
Legacy 13-label examples cover 127 boards. All 6/8/13 operational partitions cover 286.
Retain this as the historical audit; EXP-003 documents the later A-high precedence v2.

### EXP-002 — bounded architecture comparison
Script: `tools/universal_strategy/experiments.py --stage architectures`.
GHA 34160712982; code dc66bcb055d26dd68572d91e08458a6a430fe379.
Reports: `experiments/EXP-002.json`, `.md`, `maps/`.
The specified 2/4 shared-action architectures failed the published screening budgets on all three fixed grids. This does not prove adaptive exploitability or rule out every conceivable human architecture.
One shared UTG BET policy has an unavoidable overall target-frequency error of at least 16.61pp in one of the two UTG bet spots. Shared taxonomy remains possible.

### EXP-003 — bounded fixed-grid candidates
Script: `tools/universal_strategy/experiments.py --stage candidates`.
GHA 34160712982; code dc66bcb055d26dd68572d91e08458a6a430fe379.
Reports: `experiments/EXP-003.json`, `.md`, `maps/`.
Saved automatic selection: six classes, six maps, ten mixed cells; all numeric screening gates passed. Eight/thirteen-class candidates also passed but had higher complexity scores. Manual review below blocks final adoption of the selected rules; original numerical results remain unchanged.

## Manual review of EXP-003 — no experiment rerun
Source snapshot: 56565d8e8e9a8ff6a77c0b24d76b3f80c97c787a.
Downloaded GHA artifact 10032542408 from run 34160712982 and checked that its EXP-001/002/003 JSON Git blob hashes match the remote snapshot:
- EXP-001: 0546be91d5b00c3d67f831b12777dd5c3b2b134a
- EXP-002: da877b30c2c17e89397d2b657b5aa5a6620089f3
- EXP-003: 469143e11789a56e3e6863481eeddc008c5a4356
Only saved outputs were inspected, indexed and formatted; no dataset EV/frequency computation was repeated.

### All ten saved MIX cells
These are an inventory of the candidate, not newly approved rules. Rows 2-10 belong to the shared BB_DEF33 + UTG_DEF33 map.

| # | Map | Flop | Hand | Exact action |
|---|---|---|---|---|
| 1 | UTG_BB_BET | A[T-2]x | Top pair | BET 75% / CHECK 25% |
| 2 | shared DEF33 | A[K-J]x | Weak pair | CALL 25% / FOLD 75% |
| 3 | shared DEF33 | A[K-J]x | Combo draw | RAISE 25% / CALL 75% |
| 4 | shared DEF33 | A[K-J]x | OESD | RAISE 75% / CALL 25% |
| 5 | shared DEF33 | A[K-J]x | Gutshot | RAISE 25% / CALL 75% |
| 6 | shared DEF33 | A[T-2]x | Second pair | RAISE 25% / CALL 75% |
| 7 | shared DEF33 | BBx | Weak pair | CALL 50% / FOLD 50% |
| 8 | shared DEF33 | K[9-2]x | Top pair | RAISE 25% / CALL 75% |
| 9 | shared DEF33 | K[9-2]x | BDFD | CALL 75% / FOLD 25% |
| 10 | shared DEF33 | [7-4]x | A-high | CALL 75% / FOLD 25% |

No saved single-cell ablation establishes the marginal price of removing each MIX. Do not invent that price from overall regret.

### Conspicuous rules and composition problems
- BTN_DEF33: Air / Nothing = CALL on every class. Saved by_hand solver F/C/R = 91.76/6.27/1.97%, human = 0/100/0%. Category share 2.7914% of this study's reach; category local regret 0.381997bb. This is a concrete reason to reject the package as a final human policy, not merely an aesthetic complaint.
- BTN_DEF33 on A[K-J]x: Two pair+ = CALL but BDFD = RAISE. This is an awkward isolated bluff rule; its cell-specific price is not supplied by by_hand overall metrics. Flag for review, not automatically declare every such raise wrong.
- Shared DEF33: Third pair = RAISE on A[K-J]x and K[9-2]x while stronger pair rows call or mix. BDFD pattern = F/F/F/C75/F/C. These are exceptions, not clean action regions; no new rule is endorsed here.
- UTG_BB_BET: Gutshot solver BET 84.83% -> human 0%, category local regret 0.006576bb. BDFD solver BET 60.78% -> human 0%, category local regret 0.004288bb. Overall BET 62.8% -> 65.1% does not establish preserved composition. On [7-4]x Two pair+/OESD CHECK while all three board-pair rows BET: another non-monotone region.
- UTG_BTN_BET: saved Draws BET action mass falls from 8.59% to 1.41% of total study reach, while Pairs BET mass rises from 15.08% to 22.79%. The near-matching overall BET masks this change. Do not assert that local regret alone validates it.
- BTN_STAB: BDFD has B/B/B/X/B/B across the six columns, an isolated K[9-2]x check. A-high always CHECK while Air BETs on [Q-8]x/[7-4]x. These are observed departures from a simple monotone layout, not proof of expensive errors by themselves.

### Meaningful error concentrations (copied from saved JSON)
Source locations: `grids.six.maps[*].metrics[study].by_hand` and `.by_flop`.
Local regret is conditional on the named category, not its contribution to the whole study.

| Study / category | Share of study reach | Category local regret, bb | Problem |
|---|---:|---:|---|
| BTN_DEF33 / Air | 2.79% | 0.38200 | CALL 100% versus solver FOLD 91.76% |
| BB_DEF33 / A-high | 7.15% | 0.11629 | FOLD 97.23% versus solver 55.05% |
| UTG_DEF33 / A-high | 17.87% | 0.11126 | FOLD 88.55% versus solver 55.70% |
| UTG_DEF33 / BDFD | 9.68% | 0.08370 | FOLD 92.70% versus solver 56.42%; no BDFD raises retained |
| BB_DEF75 / Combo draw | 5.73% | 0.14079 | RAISE 100% versus solver 38.98% |
| BB_DEF75 / 2 overcards + draw | 4.52% | 0.13611 | F/C/R 12.14/79.39/8.48 versus solver 59.83/25.74/14.43 |
| UTG_DEF33 / [Q-8]x | 59.24% | 0.04577 | Broad, materially weighted class, not a negligible rare board |
| BB_DEF75 / [7-4]x | 2.19% | 0.09483 | Explicitly expensive low-board class |

Tail metrics are action-probability-weighted masses, not simple combo counts:

| Study | Overall local regret, bb | Extra loss vs exported mixed, bb | Action mass loss >0.5bb | Action mass loss >1bb |
|---|---:|---:|---:|---:|
| UTG_BB_BET | 0.00331 | 0.00022 | 0.0039% | 0.0001% |
| BB_DEF33 | 0.02742 | 0.02204 | 1.1344% | 0.2184% |
| UTG_DEF33 | 0.03665 | 0.03372 | 1.9595% | 0.0607% |
| BB_DEF75 | 0.03004 | 0.02620 | 1.8253% | 0.6074% |
| UTG_BTN_BET | 0.00593 | -0.00124 | see EXP-003.json | see EXP-003.json |
| BTN_DEF33 | 0.02990 | 0.02199 | 1.5301% | 0.3048% |
| BTN_STAB | 0.00283 | 0.00037 | 0% | 0% |

Do not conflate a rare maximum with a material category error. For example BTN_DEF33's worst saved board 9s 5h 4d has 0.75853bb conditional regret but only 0.01374% of study reach; its [7-4]x class has 0.15015bb regret but only 0.4552% reach. In contrast UTG_DEF33 A-high is 17.87% reach. Saved maximum combo regret has no combo identifier in the report; do not fabricate one.

### Why numeric PASS did not settle manual acceptance
optimize.py checks overall/class averages, costly action masses and broad composition groups; it does not impose monotone hand actions. The composition filter combines rows 12/13/14 (2OC, A-high, Air); the 0.20bb per-cell cap only applies where a single flop/hand cell has >=2% of total study reach. Therefore a bad whole hand row spread across smaller cells can survive. This is a limitation of the screening/acceptance policy, not evidence that dataset arithmetic or the GPU solve is corrupt.
Preserve EXP-001/002/003; do not erase or rerun them merely because manual review rejects a candidate.

## Current best candidate
Six-axis taxonomy retained provisionally. The saved six-map/ten-MIX package is an experimental baseline only and is NOT approved for insertion into strategy_structured.md. Manual blockers are recorded above. Do not claim near-GTO, full protection from exploitation, an optimal rule count, or that all ten MIX cells are necessary.

## Rejected ideas
- Unbounded category search for tiny EV gains: rejected by user constraint, not by experiment.
- Treating a green optional-script workflow step as proof of a completed analysis: invalid.
- Assuming screenshot-only comparisons are reproducible: invalid until supported by committed code/results.
- Treating six maps as inherently easier than seven: invalid without comparing total rules/MIX and semantics.
- Approving the current BTN Air = CALL row because overall regret is below 0.04bb: rejected by this manual review.
- Treating odd/non-monotone actions as automatically expensive without local data: also invalid; distinguish quantified errors from qualitative cautions.

## Next step
After a NEW user message authorizes continuation, run ONE targeted candidate comparison only: retain the entire EXP-003 six-class/six-map package and change BTN_DEF33's Air / Nothing row from CALL to FOLD across all six flop classes. Keep all other cells, ranges, definitions and maps unchanged. Compare the complete modified BTN policy with the saved baseline for local regret, class/overall frequencies, composition and costly tails. Save as a new experiment; do not rerun EXP-001/002/003 or perform a broad search. Do not claim this edit is validated before computing it. Stop after that single comparison and checkpoint. The existing workflow runs both old experiment stages, so do not dispatch it unchanged for this targeted step; use an isolated stage/workflow. Current turn ends with this manual-review checkpoint.

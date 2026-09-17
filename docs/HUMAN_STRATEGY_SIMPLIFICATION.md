# Human strategy simplification

## 1. Purpose

The generated workbook is the reproducible solver-frequency baseline. A human
strategy is a separate interpretation layer whose goal is to reduce decisions
without hiding material changes in frequencies or EV.

The supported generator stops at the solver-frequency workbook. It never
creates, updates or consumes a human strategy. Human simplification is performed
manually after generation by an analyst using the rules below. Temporary local
calculations may support that review, but no study-specific human-table
generator belongs in the production scripts.

## 2. Authoritative inputs

Use tracked combo-level solver outputs and the generated `strategy-10`
details. Never infer solver frequencies or EV from displayed labels alone.

The source study fixes positions, ranges, boards, tree and bet sizes. Do not
transfer a rule between UTG-vs-BB and UTG-vs-BTN without recalculating it from
that study's own data.

The mutually exclusive display priority remains:

1. OESD;
2. Gutshot;
3. made hand;
4. two overcards plus BDFD;
5. Air.

A pair with OESD is OESD. A pair with a gutshot is Gutshot. A pair without
either direct draw stays in its made-hand category. This priority must be used
for both the baseline workbook and every simplification audit.

## 3. Simplification objective

Prefer the smallest rule set that remains recognizably close to the solver.
Test simplifications in this order:

1. one action for an entire hand row;
2. if needed, one boundary between A-high and non-A-high flop groups;
3. if needed, one boundary between high and middle/low flop groups;
4. only then isolate `ABB` or `BBB` as a special case;
5. add a conditional selector such as `BDFD` only when combo data proves that
   the condition separates continue from fold.

A monotone left-to-right boundary is preferable to alternating actions. Do not
force monotonicity when a large frequency or EV discontinuity shows that an
exception is real.

A slash label in the generated workbook means a strict 50/50 randomizer between
the two displayed actions. A conditional human rule is not a randomizer and
must have its own legend, for example `BDFD`: CALL with a backdoor flush draw,
otherwise FOLD.

## 4. Candidate construction

For each branch, hand row and flop group:

1. reproduce the baseline combo-then-board action means from section 7 of
   `FLOP_STRATEGY_WORKFLOW.md`;
2. retain combo counts and board counts;
3. inspect action composition by board, pair rank, kicker and draw subtype;
4. propose the coarsest rule supported by those distributions;
5. evaluate the proposed action against the solved opponent using the existing
   reach-weighted local-regret calculation;
6. compare the candidate with both the solver frequencies and generated
   workbook policy.

Reach probability is used for the EV audit and for explicitly labelled
node-wide frequency metrics. It does not replace the baseline cell aggregation
rule.

Solver frequency chooses ordinary actions. EV is an audit and safety veto; it
must not be used to invent an action that the frequency data does not support.
Do not call local regret exploitability.

Theory may explain an accepted data-backed rule, but must be kept separate from
the calculation. If no reliable theoretical explanation is available, state
that instead of inventing one.


## 4A. Separate procedures for initiative and defense

Both procedures start from the same tracked combo-level frequencies, pure-action
EVs and reach values. They differ in what must remain balanced and therefore
must not be collapsed into one generic cell-selection rule.

### 4A.1. Initiative: CHECK versus BET or DONK

Use this procedure when the acting player chooses between CHECK and an
initiative action such as BET or DONK:

1. Confirm the exact actor, opponent, pot, size and upstream path. Do not mix
   c-bet, stab and donk data or transfer a partition between positions.
2. Reproduce total and per-hand-row solver action frequencies, both by the
   baseline board-then-combo mean and, where labelled, by reach.
3. Start with the smallest exhaustive board-height partition. Test familiar
   boundaries such as A-high, K/Q-high, J/T-high and low boards. Test a special
   `AKx / Kxx` or low-only donk class only when the local data shows a stable
   discontinuity.
4. For every proposed class inspect value hands, ordinary pairs, OESD, Gutshot,
   `2 overcards + BDFD` and Air separately. A matching total BET frequency is
   insufficient if the candidate bets the wrong hand rows.
5. Build a coherent betting range: strong value supplies calls from worse,
   direct draws supply natural semi-bluffs, and a controlled Air component
   prevents BET from meaning only value. Preserve a protected CHECK range.
6. Test pure CHECK, pure BET/DONK and the standard 50/50 mix first. A fixed
   15/85 mix is allowed only as an explicitly audited initiative exception:
   it must represent a stable low-frequency tendency across a broad,
   memorable row or board class, be compared with 0/50/100 alternatives, and
   be written in the table and legend. Never invent arbitrary percentages per
   cell to imitate solver output.
7. A pure-value override is allowed when raw frequency and pure-action EV both
   support it and it removes a meaningful loss tail or wrong range composition.
   EV remains a veto and audit, not a source of unsupported actions.
8. Compare candidate partitions on column count, total action delta, hand-row
   and board-family composition, root loss, P95/P99/maximum loss and reach in
   the loss tails. Choose the simplest Pareto candidate whose remaining skew
   is explicit and teachable.
9. If this action leads to a later training branch, that branch may generate
   only boards and hands on which the upstream human table permits the observed
   BET or DONK. An off-policy response table may remain documented, but it must
   not create impossible standard histories.

### 4A.2. Defense and response: FOLD, CALL and RAISE

Use this procedure after an opponent BET, DONK or RAISE:

1. Confirm the exact node and legal actions. Treat a response to a first bet
   separately from a response in a deep, low-reach raise branch.
2. Establish the coarse human skeleton before adding exceptions: normal made
   hands tend to CALL, hands without sufficient equity tend to FOLD, and the
   raising range is built primarily from strong value, OESD and Gutshot.
3. Audit pair rank, kicker band, made pair inside a draw row, direct-draw
   subtype and BDFD. Add a selector only when one visible property reliably
   separates valid continues from folds.
4. Prefer a deterministic strength boundary to random CALL/FOLD. A human
   `C/F` or `F/C` cell therefore requires a local legend stating which stronger
   subgroup calls and which weaker subgroup folds; it is not automatically a
   50/50 randomizer. `C/R` and `R/C` remain exact 50/50 unless their local
   legend explicitly says otherwise.
5. Start the board search with tight Broadway, remaining high boards and low
   boards as hypotheses, not universal categories. Merge Axx with Bxx only
   after their final hand-row actions and hidden subgroups have been checked
   separately. Keep `ABB / BBB` isolated when it has a real discontinuity.
6. Do not restore rare solver raises with pairs or Air merely to match the
   aggregate raise percentage. The simplified raise range may intentionally
   concentrate in value and direct draws when frequency, fixed-opponent EV and
   tails remain acceptable.
7. In a rare deep branch, simplify more strongly toward value and robust draws.
   Record the branch reach and the cost of discarded marginal continues rather
   than carrying the full first-response complexity into the table.
8. Re-run the complete frequency, composition and local-regret audit after
   every merge or selector. Use only branch-specific, explicitly approved
   tolerances; there is no universal frequency or EV allowance.

These procedures produce proposals only. The analyst presents the exact table,
audit and known distortions; only explicit user approval makes it the recorded
human strategy. No repository generator performs these judgments.


## 5. Required audit

Every proposed human table must report, for each branch:

- solver and simplified overall action frequencies;
- absolute frequency deltas for FOLD/CALL/RAISE or CHECK/BET;
- populated and absent cells;
- combo and reach coverage;
- total reach-weighted local regret in big blinds;
- mean and maximum local regret;
- counts and reach mass above 0.10, 0.25 and 0.50 bb;
- the worst cells and worst concrete combos;
- results of every conditional selector such as BDFD;
- any isolated `ABB` or `BBB` exception.

Also inspect subgroup errors. Similar overall frequencies can conceal a serious
mistake in a specific board family, kicker band or draw subtype.

Reject or revise a candidate when it creates an unsupported pure action,
depends on a tiny or unstable sample, produces a concentrated loss tail, or
moves a strategically important subgroup in the wrong direction.

No universal numeric acceptance threshold is added here. Use only thresholds
already fixed in the generator or explicitly approved for the human phase.

## 6. Deliverables and approval

Keep these layers distinct:

- `strategy-10/` and the final workbook: reproducible generated baseline;
- human candidate table: a manually prepared Markdown teaching artifact;
- human audit: calculations and a written explanation used during review;
- approved human strategy: the exact table explicitly accepted by the user.

There is no automated simplifier and no human-candidate generator. Rebuilding a
study always produces only the solver-frequency baseline and its validations.
Approval of a Markdown table does not add it to the Excel generator.


## 7. Exact analysis dataset

A human-table analysis starts from one branch's tracked aggregate `combos.csv`.
For every active concrete combo retain the board, cards, source weight, node
reach probability, solver action frequencies, mixed EV, every pure-action EV,
made-hand base, direct-draw class and BDFD flag. Re-run the repository
classifier; do not trust categories copied from an earlier workbook.

For hand row `h`, board `b` and action `a`, first compute the ordinary
combo mean on that board, then the ordinary mean of those board means inside
each proposed flop class. This is the policy signal. Source weights and reach
magnitude do not change it. Keep counts of boards, concrete combos and reach
beside every estimate so tiny subgroups remain visible.

The candidate policy is evaluated per concrete combo. If its action
probabilities are `q[a]`, then:

```text
candidate_ev = sum(q[a] * pure_action_ev[a])
combo_loss_bb = max(0, solver_mixed_ev - candidate_ev) / 10
mean_local_loss_bb = sum(reach * combo_loss_bb) / sum(reach)
```

Also report root-normalized loss using the original flop-root reach denominator.
These are fixed-opponent local-regret measurements, never exploitability.


## 8. Finding learnable flop classes

Start with B13 because it assigns all 286 boards deterministically. A candidate
partition may merge B13 members or use explicit rank rules, but it must be
mutually exclusive, exhaustive, stable under suits and verified against the
board file. Print every class definition and board count; counts must sum to
286. Names such as `Axx`, `B[Q-8]x` or `[9-2]x con` are not accepted until
their exact inclusion and exclusion rules are written down.

Search candidate partitions from the smallest user-approved column count
upward. Prefer familiar boundaries: ace-high versus non-ace-high, high versus
low middle card, and connected versus disconnected low boards. Merge only
classes whose hand-row action vectors and subgroup composition are similar.
Isolate `ABB` or `BBB` when the raw data shows a real discontinuity.

For every partition, rebuild every cell from raw frequencies and calculate the
full audit. Keep the Pareto set rather than optimizing one magic score:
column count, populated cells, node-wide action deltas, mean and root loss,
P95/P99/maximum loss, reach mass above 0.10/0.25/0.50 bb, row/action error and
action-range composition error. The chosen partition is the simplest member
whose remaining errors are understood and teachable.

A four-column result is not automatically better than an eight-column result.
Reject a merge when an apparently good total frequency hides a wrong `ABB`,
`BBB`, pair-rank, kicker, made-pair-with-draw or BDFD subgroup.


### 8.1. Canonical teaching grid

The human-facing layer uses six shared classes with two canonical orders:

- initiative: `ABB, Axx, BBB, K/Qxx, J/Txx, [9-2]xx`;
- defense/response: `ABB, BBB, Axx, K/Qxx, J/Txx, [9-2]xx`.

Initiative keeps ace-high boards together. Defense puts the two
dense-Broadway exceptions together so that they do not create misleading
alternating action patterns.

This is a display standard, not a universal solver partition. Internal audits
must retain B13 or any finer split needed to expose subgroup errors. Exact
definitions, classification precedence, counts, exceptions, reachability and
the Markdown/trainer synchronization checklist are in
`docs/UNIFIED_FLOP_GRID.md`.


## 9. Cell policy and subgroup selectors

The default ordinary cell policies are one pure action or an exact 50/50 mix
of two displayed actions. `B/X`, `D/X`, `C/R` and their reversed forms are
50/50; slash order follows solver majority and does not change the randomizer.
A human `C/F` or `F/C` must instead have a local deterministic strength
selector unless it is explicitly declared to be a randomizer. Initiative
tables may use a labelled 15/85 mix only under the exception in section 4A.1.
Three-way mixes and unlabelled or board-specific percentages are not allowed.

Against the same fixed opponent strategy, the EV of any fixed mix is the
weighted average of its pure-action EVs. It therefore cannot beat every pure
component on mean local EV. Retain a mix only for an explicitly audited
frequency, range-composition or tail-risk reason; never describe it as the
local-EV optimum when a pure action is better.

During manual analysis, temporary calculations enumerate each one-hot pure
action and every 50/50 pair of legal actions first. An initiative analysis may
then test the explicit 15/85 exception against those standard alternatives.
The analyst compares those vectors with the cell's solver frequencies; this
calculation proposes candidates but does not generate or approve the teaching
table. Use fixed native action order only to break an exact tie. At a
two-action node the default candidate mapping
is the nearest 0/50/100 rule: up to and including 25% for the second native action
maps to the first pure action, 75% or more maps to the second pure action, and
the interior maps to 50/50. Any different boundary is an explicitly named
experiment, never a silent global change.

For a human candidate, compare the nearest 0/50/100 bucket with the generated
65% baseline, but do not adopt a new threshold globally from one branch. A
pure override is allowed only when raw frequencies support that action and a
50/50 randomizer demonstrably selects the wrong half of the combos.

Audit each hand row by board class, pair rank, kicker band, direct-draw subtype,
made pair inside a draw row and BDFD. For each action, compare the solver and
candidate distribution of the action range across hand rows and flop classes.
Report percentage-point deltas and total-variation distance. This composition
audit is mandatory because matching F/C/R or X/B totals can still select the
wrong hands.

A selector must be observable at the table and use the same classifier
priority. Preferred selectors are `BDFD`, made pair inside Gutshot, a simple
kicker band or one explicit flop exception. Record both sides' frequency,
reach, EV loss and sample size. If the split is unstable or complicated, keep
the broader 50/50 cell rather than inventing a mnemonic.


## 10. Astra review contract

GPT-6 Astra is a second analyst, not a data source and not an approver. Use it
after the primary analysis has produced reproducible candidate metrics. Give it
a compact review package containing:

- branch, actor, legal actions and exact study/range/board provenance;
- classifier priority and exact candidate flop definitions/counts;
- baseline and candidate action-frequency, regret, tail and composition metrics;
- cell-level frequencies and support for the leading candidates;
- worst cells, worst concrete combos and every proposed selector;
- the user's complexity limit and invariants that may not be changed.

Ask Astra to look independently for hidden clusters, non-monotone exceptions,
wrong-action subgroups and simpler partitions. It may propose tests, but its
numbers and conclusions are never copied into production. The primary process
must reproduce every accepted claim from tracked combo data and rerun the full
audit. If Astra, theory and local data disagree, local data wins. Astra never
edits the canonical workbook, never launches the solver and never declares a
candidate approved.


## 11. Recorded worked examples

These examples record how the method was applied; they are not automatic
production policies.

For STU004 `04_UTG_AFTER_STAB`, a reviewed five-class partition was:
`Axx` (66), `B[Q-8]x` (104), `B[7-3]x` (60),
`[9-2]x dis` (40), and `[9-2]x con` (16). It reduced populated cells from
103 to 56. Solver F/C/R was 40.02/48.10/11.88%; the candidate was
43.27/44.52/12.21%. Mean local loss was 0.01345 bb and P99 was 0.36769 bb.
The remaining known skew was over-raising Two pair+ and Gutshot while always
folding Air.

For STU002 `03_BB_AFTER_CBET`, four-to-six-class merges were rejected because
they hid third-pair and OESD discontinuities on `ABB`/`BBB`. The reviewed
eight classes were `ABB` (6), `A[K-T]x` (32), `A[9-2]x` (28), `BBB`
(4), `B[Q-8]x` (100), `B[7-3]x` (60), `[9-8]xx` (36), and
`[7-4]xx` (20). The reviewed candidate used a made-pair selector for
Gutshot on ABB, BDFD where proven, and pure CALL for Second pair on
`A[K-T]x` because a random 50% fold selected the wrong BDFD combos. It moved
baseline mean loss from 0.02516 to 0.01460 bb and P99 from 0.637 to 0.444 bb.
Gutshot composition inside the raise range remained the main caveat.

The approved STU002 defensive candidate displays three classes:
`ABB / BBB` (10), non-ABB/BBB `Axx / Bxx` (220), and `[9-2]xx` (56).
The audit still checks Axx and Bxx separately, but their final action vectors
are identical, so the display merge changes no action or metric. The table was
produced by manual review of tracked combo data; it is not generated by a
repository script. Solver F/C/R is
47.90/39.09/13.01%; the candidate is 51.23/37.91/10.86%. Mean source-mix
loss is 0.013265 bb, clipped source loss is 0.013848 bb, and oracle-regret
P95/P99 is 0.033336/0.431487 bb.

The final design deliberately keeps the human check-raise range concentrated
in strong value, OESD and Gutshot. Rare solver raises with pairs or Air are not
restored merely to match composition. The shared `PAIR` selector on
`Gutshot / ABB / BBB` calls made pairs and folds unpaired Gutshots. Exact
history, Astra's role, subgroup vetoes, branch-specific guardrails and the
repetition protocol are recorded in `docs/BB_DEFENSE_SIMPLIFICATION.md`.

For STU002 `05_UTG_AFTER_DONK`, the approved manual table uses three classes:
`ABB / BBB`, non-ABB/BBB `Axx / Bxx`, and `[9-2]xx`. Solver F/C/R is
28.04/59.03/12.93%; the candidate is 37.29/52.72/9.99%. Root source/clipped
loss is 0.003877/0.008518 bb, both lower than the previous five-column teaching
table. The explicit cost is over-folded Air and a raise range concentrated in
Two pair+, OESD, Gutshot and low-board Top pair. Full evidence and Astra review
are recorded in `docs/UTG_DONK_RESPONSE_SIMPLIFICATION.md`.

For the low-reach STU002 `06_BB_AFTER_DONK_RAISE` branch, the same three classes
support a stronger value-and-draw simplification with pure CALL/FOLD decisions.
The only row-wide selectors are `PAIR/BDFD` for Gutshot and `Ax` for two
overcards plus BDFD. Solver F/C is 41.48/58.52%; the approved candidate is
40.59/59.41%, with root source/clipped loss of 0.000282/0.000298 bb. The exact
table, rare-branch rule, tail cost and Astra review are in
`docs/BB_DONK_RAISE_RESPONSE_SIMPLIFICATION.md`.

For STU004 `04_UTG_AFTER_STAB`, the approved manual table uses four
classes: `ABB / BBB`, non-ABB `Axx`, non-BBB `Bxx`, and `[9-2]xx`.
Solver F/C/R is 40.02/48.10/11.88%; the candidate is
41.94/45.97/12.10%. Root clipped loss is 0.004649 bb, lower than the former
five-column teaching table's 0.006339 bb, while P99 falls from 0.441121 to
0.361774 bb. The exact table, rejected three-class merge, deliberate range
distortions and Astra review are recorded in
`docs/UTG_STAB_RESPONSE_SIMPLIFICATION.md`.

For STU004 `03_BTN_AFTER_CBET`, the approved manual table uses three
classes: `ABB / BBB`, non-ABB/BBB `Axx / Bxx`, and `[9-2]xx`.
Solver F/C/R is 34.84/52.43/12.73%; the candidate is
39.92/52.06/8.03%. Root source/clipped/oracle loss is
0.002372/0.003410/0.005520 bb. The only deterministic CALL/FOLD selector is
the row-wide Weak-pair rank boundary. The exact table and audit are in
`docs/BTN_CBET_RESPONSE_SIMPLIFICATION.md`.

For STU005 `03_BB_AFTER_CBET`, the approved manual table uses the canonical
six defense columns. Solver F/C/R is 43.14/45.71/11.16%; the candidate is
50.56/41.22/8.22%. Mean local source loss is 0.017993 bb and local oracle-
regret P99 is 0.561649 bb. Dense Broadway Third pair uses the row-wide `BDFD`
selector and dense Broadway Gutshot uses `PAIR`; all remaining transitions are
pure actions or exact 50/50 CALL/RAISE mixes. The exact table and audit are in
`docs/BB_CBET_RESPONSE_VS_BTN_SIMPLIFICATION.md`.

For STU005 `04_BTN_AFTER_CHECK_RAISE`, the approved manual table keeps the
canonical six defense columns. Solver F/C is 40.07/59.93%; the candidate is
42.29/57.71%. Local source loss is 0.023685 bb, but the branch reaches only
6.04% from the flop root, giving root-normalized loss of 0.001431 bb. Dense
Broadway pairs use `BDFD`, dense Broadway Gutshot uses `PAIR`, Low pocket pair
and Air fold, and all normal pairs plus direct draws call from Axx downward.
The exact table and rejected Gutshot micro-rule are recorded in
`docs/BTN_RESPONSE_TO_BB_CHECK_RAISE_SIMPLIFICATION.md`.

For STU005 `05_BTN_AFTER_DONK`, the approved manual table keeps the canonical
six defense columns. Solver F/C/R is 29.25/54.25/16.50%; the candidate is
38.80/49.27/11.93%. Mean local source loss is 0.017220 bb and local oracle-
regret P99 is 0.599497 bb. Two pair+, OESD and Gutshot use a uniform exact
50/50 CALL/RAISE mix; ordinary pairs call; Low pocket pair folds; Third pair
on dense Broadway and Air from Axx downward use `BDFD`.

Baseline `5.4.1` makes BB range CHECK, so this branch has zero reach against
the approved human baseline. The user explicitly approved it as an all-six-
class opponent-deviation trainer exercise against humans who may donk anyway.
That exception is branch-specific and does not change the upstream strategy
or make other off-policy branches reachable. The exact table and audit are in
`docs/BTN_RESPONSE_TO_BB_DONK_SIMPLIFICATION.md`.

For STU005 `06_BB_AFTER_DONK_RAISE`, the approved manual table keeps the
canonical six defense columns. Solver F/C is 41.91/58.09%; the candidate is
33.61/66.39%. Mean local source loss is 0.048328 bb, but the branch reaches
only 0.4122% from the solved flop root, giving root-normalized source loss of
0.000199 bb. Strong value and OESD call, weak pocket pairs and Air fold, while
Second pair, Third pair and Gutshot use simple strength transitions.

This branch is generated only downstream of the approved `5.4.5` opponent-
deviation exercise when BTN raises. Because that parent can raise on every
class, the trainer must support `5.4.6` on all six classes as part of the same
human-donk deviation mode. The exact table, rejected low-board Third-pair
exception and audit are recorded in
`docs/BB_RESPONSE_TO_BTN_DONK_RAISE_SIMPLIFICATION.md`.

The initiative procedure is represented by four approved worked examples:

- STU002 `01_BB_FIRST` keeps T-high and higher as range CHECK, uses a broad
  15% donk on `[9-8]xx`, and raises suitable `[7-4]xx` rows to 50%. The two
  low classes are necessary because one merged low class hid opposite board-
  height errors. See `docs/BB_DONK_SIMPLIFICATION.md`.
- STU002 `02_UTG_AFTER_CHECK` uses A-high, K/Q-high, J/T-high and 9-high-or-
  lower. The fourth column is retained because Low pocket pair and Overpair
  change materially at the lowest boundary. See
  `docs/UTG_CBET_VS_BB_SIMPLIFICATION.md`.
- STU004 `01_UTG_FIRST` uses `AKx / Kxx`, remaining A/Q/J-high and T-high-or-
  lower. Strong value pure-bets the first class, ordinary rows retain simple
  mixes, and the entire lowest class checks. See
  `docs/UTG_CBET_VS_BTN_SIMPLIFICATION.md`.
- STU004 `02_BTN_AFTER_CHECK` uses A-high, K/Q-high and J-high-or-lower.
  Pure value and the supported A-high Gutshot override repair the dominant
  loss and composition errors without adding another column. See
  `docs/BTN_STAB_VS_UTG_SIMPLIFICATION.md`.

These examples show the initiative workflow rather than a universal partition:
each split and override was accepted only after its own frequency, composition
and fixed-opponent EV audit.

Do not transfer any recorded partition to another branch without recalculation.


## 12. Permanent separation from generated output

The repository generator has one responsibility: convert tracked solver data
into the canonical solver-frequency workbook. It does not know about approved
Markdown tables and never emits a human strategy.

Human tables are maintained as manually reviewed documentation. Their process
is repeatable because the source data, classification rules, audit formulas,
Astra review contract, accepted exceptions and final tables are written down.
Repeatability does not mean implementing the judgment as a generator.

The files formerly named
`output/STU004_UTG_vs_BTN_UTG_cbet_test.xlsx` and
`output/STU002_UTG_vs_BB_human_strategy_candidate.xlsx` were experiments and
are not sources of truth. Rebuilding any study continues to produce only the
solver-frequency baseline and its existing validations.

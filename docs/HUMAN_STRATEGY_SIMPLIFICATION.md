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


## 9. Cell policy and subgroup selectors

Allowed ordinary cell policies are one pure action or an exact 50/50 mix of
the two displayed actions. The slash order follows solver majority; it does
not change the randomizer. Three-way mixes and remembered board-level
percentages are not allowed.

Against the same fixed opponent strategy, the EV of an exact 50/50 mix is the
average of the two pure-action EVs. It therefore cannot beat both pure actions
on mean local EV. Retain a mix only for an explicitly audited range-composition
or tail-risk reason; never describe it as the local-EV optimum when a pure
action is better.

During manual analysis, temporary calculations may enumerate each one-hot pure
action and every 50/50 pair of legal actions. The analyst compares those vectors
with the cell's solver frequencies; this calculation proposes candidates but
does not generate or approve the teaching table. Use fixed native action order
only to break an exact tie. At a two-action node this
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

The approved STU002 defensive candidate uses four classes: `ABB / BBB`
(10), `Axx` excluding ABB (60), `Bxx` excluding BBB (160), and
`[9-2]xx` (56). It was produced by the documented manual review of the
tracked combo data; it is not generated by a repository script. Solver F/C/R is
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

# Human strategy simplification

## 1. Purpose

The generated workbook is the reproducible solver-frequency baseline. A human
strategy is a separate interpretation layer whose goal is to reduce decisions
without hiding material changes in frequencies or EV.

The current generator stops at the approved workbook. It must not overwrite
that workbook with a human simplification. A future iteration may produce a
separate candidate and audit only after that output is explicitly requested.

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
- human candidate table: separate Markdown or workbook artifact;
- human audit: machine-readable metrics and a short explanation;
- approved human strategy: created only after review.

A future automated simplifier may generate the candidate and audit, but it must
not silently replace the baseline or declare the candidate approved. Until that
automation is explicitly enabled, regeneration produces only the baseline
workbook and its existing validations.

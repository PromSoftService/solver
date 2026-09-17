# Canonical six-class teaching flop grid

## 1. Purpose

This document records how the shared human-facing flop grid was obtained and
how it must be used in Markdown strategy tables and the standalone trainer.

The six shared classes are:

| Teaching class | Boards |
|---|---:|
| `ABB` | 6 |
| `BBB` | 4 |
| `Axx` | 60 |
| `K/Qxx` | 96 |
| `J/Txx` | 64 |
| `[9-2]xx` | 56 |
| **Total** | **286** |

The classes are common, but their display order depends on the decision type:

| Decision type | Canonical display order |
|---|---|
| Initiative: CHECK versus BET/DONK | `ABB -> Axx -> BBB -> K/Qxx -> J/Txx -> [9-2]xx` |
| Defense/response: FOLD, CALL, RAISE | `ABB -> BBB -> Axx -> K/Qxx -> J/Txx -> [9-2]xx` |

Initiative keeps the ace-high classes adjacent before moving through
non-ace-high boards. Defense puts the two dense-Broadway exceptions next to
each other before the ordinary height progression.

This is a teaching and interface coordinate system. It is not a replacement
for B13, not a solver output and not a universal strategy. Identical columns
allow positions and branches of the same decision type to be compared without
relearning the layout; every action still has to be calculated and audited
from that branch's own tracked combo data.

## 2. Exact classification

The six classes are mutually exclusive and exhaustive over BRD001's 286
unpaired rainbow flops. Suits do not affect class membership.

Classification uses this exact precedence, independently of which display
order is used:

1. `ABB`: ace-high with both other ranks Broadway (`T` through `K`);
2. `BBB`: all three ranks Broadway (`T` through `K`) and no ace;
3. `Axx`: every remaining ace-high flop;
4. `K/Qxx`: every remaining flop whose highest rank is `K` or `Q`;
5. `J/Txx`: every remaining flop whose highest rank is `J` or `T`;
6. `[9-2]xx`: every remaining flop whose highest rank is at most `9`.

The precedence is part of the contract. In particular, `AKQ` is `ABB`, not
`Axx`, and `KQJ` is `BBB`, not `K/Qxx`. The label `[9-2]xx` is retained
for the teaching vocabulary even though an unpaired three-card flop cannot have a
highest rank below `4`.

Any implementation must verify the counts `6 + 4 + 60 + 96 + 64 + 56 = 286`
against the canonical board file. A classifier that produces different counts
is wrong.

## 3. How the grid was derived

The first approved human tables used branch-specific partitions. Initiative
tables often needed only board-height boundaries, while defensive tables
isolated dense Broadway flops and sometimes merged all other high boards.
Those tables were valid individually but created too many different column
layouts when placed in one trainer.

The unification was performed in the following order:

1. Start from the deterministic B13 partition and the already audited
   branch-specific human tables.
2. Keep `ABB` isolated because ace plus two Broadway cards repeatedly changes
   weak-pair, third-pair and direct-draw behaviour.
3. Keep `BBB` isolated for the same reason: three-Broadway flops are a small
   but strategically dense exception and must not disappear inside a generic
   Broadway class.
4. Split all remaining boards by memorable top-card bands: ace, king/queen,
   jack/ten and nine-or-lower.
5. Test every branch from its raw combo frequencies and pure-action EVs. A
   common column was retained only when its hidden subgroups and loss tails
   remained understandable.
6. Test both meaningful display sequences. One order did not remain readable
   for both action families, so the classes were unified without forcing one
   universal order.

For initiative, `ABB -> Axx -> BBB -> K/Qxx -> J/Txx -> [9-2]xx` keeps
ace-high betting decisions together and then continues down through
non-ace-high boards.

For defense and response, `ABB -> BBB -> Axx -> K/Qxx -> J/Txx -> [9-2]xx`
puts the two dense-Broadway exceptions together. This removes misleading
visual alternation such as `C -> F -> C -> F` and more often exposes a
learnable strength boundary.

Changing between these two orders changes presentation only. It does not
change class membership, any combo policy, action frequency or EV audit.

## 4. Scope and exceptions

The six-class grid with the correct decision-type order is the default display
for a full-board teaching table. Initiative and defense/response must not
silently borrow each other's order.

A table may use a smaller partition only in one of these cases:

- the branch is intentionally restricted by an upstream action;
- all six columns have the same action vector and `All flops` is an exact
  presentation collapse;
- a branch-specific audit proves that another partition is materially simpler
  or safer.

The two retained strategic exceptions that motivated the explicit rule are:

- `UTG vs BB / BB DONK 1/2`: only `[9-8]xx` and `[7-4]xx` have a teaching
  donk; T-high and higher flops are range CHECK;
- `UTG vs BTN / UTG CBET 1/2`: `AKx / Kxx`, remaining `[A/Q/J]xx` and
  `[T-4]x` preserve a real initiative discontinuity.

An `All flops` table is also allowed when it is exact, for example a range
CHECK or a hand-driven rule whose action vector does not depend on the board
class. This is a lossless collapse of the common grid, not a seventh
classification system.

No other exception is created merely because an older table used different
headings. A new exception requires a branch-specific frequency, composition
and fixed-opponent EV audit.

## 5. Display grid versus analysis partition

The displayed six classes and the internal audit partition have different
jobs:

- B13 or a finer temporary split is used to find hidden discontinuities;
- the six-class grid is used to teach, compare and render approved actions;
- a display merge is accepted only after every hidden subgroup is checked;
- the same display class may legitimately contain different actions in
  different positions or branches.

Never copy an action from UTG-vs-BB, UTG-vs-BTN or BTN-vs-BB merely because
the column name matches. The actor, preflop ranges, initiative, legal actions,
upstream history and node reach remain branch-specific.

When adjacent display classes happen to contain identical actions, keeping
both is acceptable because the stable decision-type layout reduces total
learning cost. Merging them is allowed only as a presentation shortcut and
must not erase a documented exception used elsewhere.

## 6. Reachability and off-policy columns

A response table may document all six classes even when the approved upstream
strategy reaches only a subset. Such columns describe an off-policy response
to an unexpected opponent action.

The trainer must distinguish documentation from normal-path generation:

- normal training generates only histories permitted by the upstream human
  strategy;
- off-policy columns may be shown in the reference table;
- an impossible standard history must not be generated merely because its
  response cell exists.

An approved opponent-deviation exercise is the only exception. It must be
named branch-specifically, must not alter the upstream baseline strategy and
must state exactly which otherwise off-policy classes the trainer generates.

The first such exception is BTN-vs-BB `5.4.5`: although baseline `5.4.1`
makes BB range CHECK, the trainer generates `BB DONK 1/2 -> BTN RESPONSE` on
all six classes so the user can practise against human opponents who donk
incorrectly. This does not invent a solver donk, change the normal-path tree
or automatically authorize unrelated off-policy branches.

The approved deviation path extends one step deeper only when `5.4.5`
generates BTN RAISE: the trainer then generates `5.4.6 BB RESPONSE` on all six
classes. This extension is reachable because the approved `5.4.5` table can
raise Two pair+, OESD and Gutshot in every class. It remains part of the same
named human-donk deviation exercise and does not make donk histories part of
the normal baseline.

This distinction is particularly important for donk and donk-raise branches.

## 7. Cell labels and selectors

Class unification and branch-type ordering do not change action-label semantics:

- slash labels such as `C/R`, `R/C`, `B/X` and `D/X` are exact 50/50 mixes;
- slash order records solver majority but does not change the randomizer;
- `BDFD`, `PAIR`, `PAIR/BDFD`, `Ax` and any strength boundary are
  deterministic selectors, not randomizers;
- every selector must have a local legend and must use an observable property;
- `—` means that the category is absent from the acting range at that node.

The shared hand-priority contract remains:

`OESD -> Gutshot -> made hand -> 2 overcards + BDFD -> Air`.

## 8. What every approved branch must record

A common grid is not sufficient provenance. Each approved branch document
must also record:

1. study, run, branch, actor, legal actions and exact upstream history;
2. solver and candidate action frequencies;
3. mean/root local loss, relevant tail metrics and worst cells;
4. deliberate over-folding, under-raising or range-composition distortions;
5. every selector and both sides of its subgroup audit;
6. whether all six classes are reachable on the normal human path;
7. whether the table is a proposal or user-approved;
8. any independently reviewed alternative and its locally reproduced result.

## 9. Synchronization checklist

After a table is approved:

1. update its branch-specific worked-example document immediately;
2. in the next user-facing publication pass, update the Markdown strategy;
3. in that same publication pass, update the standalone trainer with the same
   six keys and the canonical initiative or defense/response order;
4. keep legends and hand priority identical in both artifacts;
5. verify the six board counts and all 286 classifications;
6. verify table dimensions and action tokens;
7. test normal-path reachability, off-policy exclusions and every explicitly
   approved opponent-deviation exercise;
8. record the solver/candidate audit and accepted trade-offs;
9. do not change the canonical workbook or generator;
10. an approval-only commit may precede publication only when pending trainer
    synchronization is explicit; publish the strategy and trainer together.

This checklist prevents a visually correct table from drifting away from its
classifier, action semantics or reachable game tree.

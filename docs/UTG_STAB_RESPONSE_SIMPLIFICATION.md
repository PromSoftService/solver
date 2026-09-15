# UTG response to BTN stab: approved human simplification

## Scope

This is the manually reviewed teaching strategy for STU004 branch
`04_UTG_AFTER_STAB`: UTG checked, BTN stabbed one half-pot, and UTG chooses
FOLD, CALL or the native-60 RAISE.

The source is the tracked combo-level solver export. The canonical workbook,
solver data and production generator are unchanged. No script generates or
consumes this human table.

## Approved table

| Hand category | ABB / BBB | Axx | Bxx | [9-2]xx |
|---|---:|---:|---:|---:|
| Two pair+ | C | C/R | R | R |
| Overpair | — | — | C/R | C/R |
| Top pair | C | C | C | C/R |
| Underpair | — | C | C | C |
| Second pair | F | C | C | C |
| Weak pair | — | F | C | C |
| Third pair | F | C | C | C |
| Low pocket pair | F | F | F | F |
| OESD | C | C | C/R | R/C |
| Gutshot | C | C | C/R | C/R |
| 2 overcards + BDFD | — | — | C | C |
| Air | F | F | F | F |

`C/R` and `R/C` are exact 50/50 randomizers; order records the solver-majority
action. Draws retain priority over made hands.
## Flop partition

The four classes are mutually exclusive and exhaustive over all 286 BRD001
boards:

- `ABB / BBB`: the 10 paired Broadway structures;
- `Axx`: 60 ace-high boards excluding ABB;
- `Bxx`: 160 Broadway-high boards excluding BBB;
- `[9-2]xx`: 56 boards with top rank at most nine.

The three-column merge `Axx / Bxx` was rejected. It concealed opposite
patterns in important rows: Weak pair folds much more often on Axx, while
Two pair+ raises much more often on Bxx.

## Audit

Solver FOLD/CALL/RAISE is 40.0224/48.0970/11.8806%. The approved candidate is
41.9373/45.9673/12.0954%, a change of +1.9149/-2.1297/+0.2148 percentage
points.

Mean fixed-opponent local loss is 0.011556 bb from the saved source mix,
0.012171 bb clipped, and 0.013530 bb against the best saved pure action.
Root-normalized source/clipped/oracle values are
0.004414/0.004649/0.005168 bb. Oracle-regret P95/P99 is
0.041104/0.361774 bb; 0.5373%/0.0735% of reach exceeds 0.5/1.0 bb, and the
maximum combo loss is 2.384909 bb.

The prior five-column teaching table had root clipped loss 0.006339 bb,
P99 0.441121 bb, 0.7182% of reach above 0.5 bb and maximum loss 4.680100 bb.
The four-column table is therefore both smaller and better on every reported
EV-tail measure.
## Deliberate simplifications

- Raises are concentrated in Two pair+, Overpair, low-board Top pair, OESD and
  Gutshot. Rare solver raises with weaker pairs, two overcards plus BDFD and
  Air are omitted.
- Two overcards plus BDFD pure-calls even though the solver sometimes folds or
  raises them; Air pure-folds even though the solver sometimes continues.
- `Two pair+ / Axx = C/R` is retained because its root clipped cost versus
  pure CALL is only about 0.000007 bb while it materially reduces the worst
  combo tail.
- No hidden kicker, suit or cell-specific selector is used.

GPT-6 Astra independently reviewed the reproduced metrics and accepted the
four-class partition unchanged. It identified raise-range composition and the
two-overcards/Air offset as the main remaining risks; local subgroup and tail
checks did not justify another visible rule.

This approval is branch-specific and must not be transferred to another study
without recalculation.

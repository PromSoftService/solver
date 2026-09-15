# BTN response to UTG c-bet: approved human simplification

## Scope

This is the manually reviewed teaching strategy for STU004 branch
`03_BTN_AFTER_CBET`: UTG c-bets one half-pot and BTN chooses FOLD, CALL or
the native-60 RAISE.

The only numerical source is the tracked combo-level solver export. The
canonical workbook, solver data and production generator are unchanged. No
script generates or consumes this human table.

## Approved table

| Hand category | ABB / BBB | Axx / Bxx | [9-2]xx |
|---|---:|---:|---:|
| Two pair+ | C | R/C | R |
| Overpair | — | C/R | C |
| Top pair | C | C | C/R |
| Underpair | — | C | C |
| Second pair | C | C | C |
| Weak pair | — | C/F | C |
| Third pair | C | C | C |
| Low pocket pair | F | F | F |
| OESD | C | R/C | R/C |
| Gutshot | C | R/C | R/C |
| 2 overcards + BDFD | — | C | C |
| Air | F | F | F |

`C/R` and `R/C` are exact 50/50 randomizers; order records the
solver-majority action.

`Weak pair / Axx / Bxx = C/F` is not a randomizer. CALL with a pocket pair
one or two ranks below the middle flop card; fold lower pocket pairs. Draws
retain priority over made hands.

## Flop partition

The three classes are mutually exclusive and exhaustive over all 286 BRD001
boards:

- `ABB / BBB`: 10 three-Broadway structures;
- `Axx / Bxx`: 220 other ace-high or Broadway-high structures;
- `[9-2]xx`: 56 boards with top rank at most nine.

The merge is presentation-safe for this approved table: non-paired Axx and Bxx
have the same displayed action in every hand row after applying the single
row-wide Weak-pair strength boundary.

## Audit

Solver FOLD/CALL/RAISE is 34.8385/52.4340/12.7276%. The approved candidate is
39.9157/52.0550/8.0293%, a change of +5.0772/-0.3790/-4.6983 percentage
points.

Mean fixed-opponent root-normalized loss is 0.002372 bb from the saved source
mix, 0.003410 bb clipped, and 0.005520 bb against the best saved pure action.
Local oracle-regret P95/P99 is 0.136544/0.415417 bb.

## Deliberate simplifications

- BTN almost never raises on `ABB / BBB`; made hands and direct draws remain
  in CALL while Air and low pocket pairs fold.
- On `Axx / Bxx`, raises are concentrated in Two pair+, OESD and Gutshot.
- On low boards, Two pair+ pure-raises; Top pair and direct draws retain the
  only visible 50/50 raise mixes.
- Rare solver raises with weaker pairs, two overcards plus BDFD and Air are
  deliberately omitted.
- The sole CALL/FOLD selector is observable and row-wide; no hidden kicker,
  suit or cell-specific selector is used.

The accepted candidate sacrifices raise frequency to make the range
composition learnable. Frequency totals, subgroup composition and the local
EV tail were reviewed from tracked data, and GPT-6 Astra independently
challenged the proposed merge before approval.

This approval is branch-specific. It is a manual teaching artifact and must not
be transferred to another study or generated automatically.

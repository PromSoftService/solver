# RNG002 / CFG003 / NOD003 — UTG vs BTN flop simplification

Dataset: `DS__RNG002__CFG003__NOD003__BRD001__RUN-20260907-115423.csv`.

Spot: 6-max, 100bb, UTG open 2.5bb, BTN call; TexasSolverGPU bundled preflop ranges; UTG OOP on the flop; one 33% flop bet size; `BRD001` = 286 unpaired rainbow flops.

All aggregate frequencies and losses below are weighted by `reach_probability`. `local regret` is the weighted loss from the selected simplified action mixture versus the best pure action combo-by-combo in the solved equilibrium tree. It is not a best-response exploitability measurement.

## Solver frequencies in the four human board classes

| Board class | Solver BET |
|---|---:|
| AKx | 76.6% |
| Kxx | 59.9% |
| [A/Q/J]xx | 29.1% |
| [T-4]x | 4.9% |
| Overall | 28.6% |

Equal-board averages are almost identical: AKx 76.6%, Kxx 60.1%, [A/Q/J]xx 29.5%, [T-4]x 5.0%.

This confirms the broad old structure (AK/K aggressive, A/Q/J middle, low boards mostly check) but not its exact frequencies. In the current study AKx is materially more aggressive than Kxx.

## Old user candidate as implemented

Interpretation used for evaluation:

- MIX hands: Two pair+, Overpair, Top pair, Second pair, OESD, Gutshot, BDFD, X-high;
- always CHECK: Underpair, Third pair, Air;
- MIX frequency = 80% on AKx/Kxx, 40% on [A/Q/J]xx, 0% on [T-4]x;
- `X-high` = high-card hand with at least one overcard to the flop after direct draws/BDFD take precedence;
- `Air` = high-card hand without OESD, gutshot, BDFD, or overcard.

| Board class | Solver BET | Old candidate BET | Diff | Local regret |
|---|---:|---:|---:|---:|
| AKx | 76.6% | 59.6% | -17.0 pp | 0.0206 bb |
| Kxx | 59.9% | 61.8% | +1.9 pp | 0.0145 bb |
| [A/Q/J]xx | 29.1% | 30.6% | +1.6 pp | 0.0138 bb |
| [T-4]x | 4.9% | 0.0% | -4.9 pp | 0.0001 bb |
| Overall | 28.6% | 27.6% | -1.0 pp | 0.0098 bb |

The overall frequency looks good, but it hides a large AKx distortion. The main structural issue is that Underpair and Third pair are forced to check on AKx/Kxx even though the solver bets them frequently and betting is often materially better there. Conversely, X-high is a poor generic bluff bucket on [A/Q/J]xx: solver BET is only 13.3%, average loss if checking is 0.0007bb, while average loss if betting is 0.0628bb.

Representative cell data:

- AKx Underpair: solver BET 65.4%; loss CHECK 0.0558bb vs loss BET 0.0003bb.
- AKx Third pair: solver BET 78.6%; loss CHECK 0.0368bb vs loss BET 0.0003bb.
- Kxx Underpair: solver BET 50.7%; loss CHECK 0.0423bb vs loss BET 0.0013bb.
- Kxx Third pair: solver BET 51.6%; loss CHECK 0.0378bb vs loss BET 0.0003bb.
- [A/Q/J]xx X-high: solver BET 13.3%; loss CHECK 0.0007bb vs loss BET 0.0628bb.
- [A/Q/J]xx Air: solver BET 4.8%; loss CHECK 0.0011bb vs loss BET 0.0630bb.

## Recommended same-complexity strategy

Keep the same four board classes. Change the hand composition and randomizer:

### Always CHECK

- X-high without a direct draw/BDFD;
- Air / Nothing.

### MIX pool

- Straight / Set / Two pair;
- Overpair;
- Top pair;
- Second pair;
- Underpair;
- Third pair;
- OESD;
- Gutshot;
- BDFD.

Precedence: made hand first; then OESD; then Gutshot; then BDFD; then X-high; then Air. All pocket pairs below the top flop card are `Underpair`.

Randomizer for the MIX pool:

- AKx and Kxx: BET 75% / CHECK 25%;
- [A/Q/J]xx: BET 40% / CHECK 60%;
- [T-4]x: CHECK 100%.

Result:

| Board class | Solver BET | Recommended BET | Diff | Local regret |
|---|---:|---:|---:|---:|
| AKx | 76.6% | 74.1% | -2.5 pp | 0.0125 bb |
| Kxx | 59.9% | 63.6% | +3.7 pp | 0.0094 bb |
| [A/Q/J]xx | 29.1% | 32.8% | +3.8 pp | 0.0105 bb |
| [T-4]x | 4.9% | 0.0% | -4.9 pp | 0.0001 bb |
| Overall | 28.6% | 29.4% | +0.8 pp | 0.0070 bb |

This package improves the weighted local regret from about 0.0098bb to 0.0070bb while keeping every broad class within about 5 percentage points of the solver and the overall frequency within 1 percentage point. The pure-check simplification on [T-4]x is intentionally retained: despite missing about 4.9pp of solver betting frequency, the EV cost of checking is essentially zero across the class.

## Status

The recommended strategy is a strong solver-like candidate under local EV and frequency/composition checks. It has not yet been validated against an adapting opponent with strategy locking / best response / restricted re-solve, so the local-regret numbers must not be described as exploitability or proof of near-GTO play.

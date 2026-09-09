# STU002 simplified flop strategy

## Decision rule

For each board and strict hand category, action frequencies are averaged equally
over all concrete combos with reach_probability > 0. Source-range weights and
reach magnitudes do not weight this choice. Board-level means are then averaged
equally inside the B13 flop class.

If the largest mean action frequency is greater than 65%, the
cell is pure. Otherwise the two most frequent actions become a strict 50/50 mix.
Three-way mixes are prohibited.

## EV audit

EV never selects the action. After the policy is fixed from frequencies, its
local regret is measured against the solved opponent:
max(0, solver_mixed_ev - simplified_policy_ev). EV-loss aggregates use
reach_probability and are reported in big blinds (native EV divided by 10).
This is local regret, not exploitability against an adapting opponent.

## Classification

B13 is mutually exclusive. JT9 belongs to [J-8]x con; therefore final
counts are BBx=47 and [J-8]x con=26. The other B13 counts are unchanged.

Every combo receives one base category by priority: Two pair+, Overpair, Top
pair, Second pair, Third pair, Underpair, Weak pair, 2 overcards, A-high, Air.
A direct draw modifier is none, Gutshot, or OESD; double gutshots count as OESD.
BDFD requires suited hole cards and one flop card of that suit. A made straight
does not also receive a direct-draw modifier.

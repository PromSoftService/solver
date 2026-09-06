# CFG002 — BB vs UTG c-bet 75% on BRD001

Source dataset: `datasets/DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv` (106381 combo rows, 286 canonical unpaired rainbow flops).

Comparison baseline: CFG001, same RNG001 / BRD001, UTG c-bet 33%.

Method: combo actions and EV losses are weighted by solver reach. Board-class action frequencies are computed per board and then averaged equally within each canonical rank class. Practical pure-action tolerance: 0.02bb EV loss. The goal is a human-playable solver-like strategy, not reproduction of every mix.

Board classes used here:

- `ABx` = A + K/Q/J/T + x
- `Axx` = A + 9..2 + x
- `BBx` = two non-A Broadway cards + x
- `Kxx` = K-high without a second Broadway
- `[Q-8]x`
- `[7-4]x`

## Range defense: 33% vs 75%

| Flop class | SDF vs 33 | Call vs 33 | Raise vs 33 | SDF vs 75 | Call vs 75 | Raise vs 75 |
|---|---:|---:|---:|---:|---:|---:|
| ABx | 49.2% | 36.7% | 12.5% | 35.3% | 25.4% | 9.9% |
| Axx | 58.1% | 44.5% | 13.6% | 42.4% | 35.3% | 7.1% |
| BBx | 56.3% | 42.4% | 13.8% | 40.2% | 28.7% | 11.5% |
| Kxx | 62.9% | 47.8% | 15.0% | 44.8% | 33.1% | 11.8% |
| [Q-8]x | 70.3% | 53.7% | 16.6% | 49.7% | 35.6% | 14.1% |
| [7-4]x | 72.4% | 54.1% | 18.3% | 53.6% | 38.9% | 14.7% |

The same monotonic texture trend remains: BB defends more as the board gets lower, but the 75% sizing removes roughly 14–21 percentage points of total defense depending on board class.

## Categories that must change vs the 33% strategy

The old 33% categories are too coarse for 75% in four places:

1. `Set / Two pair` must split into **Set/Trips** and **Two pair**. Their preferred pure actions diverge on Axx, BBx, Kxx and low boards.
2. `Ordinary pair` must split at least into **Top pair**, **Second pair**, **Third pair**, **High underpair**, and **Weak pocket pair**. Second/third pairs fold substantially more against 75% on high boards.
3. Generic `2 overcards + BDFD = Call` should be removed. Against 75%, backdoor-only high-card hands are usually folds; exact AK/AQ and direct-draw structure matter more than the generic two-overcards label.
4. `Gutshot` is no longer a universal call/raise bucket. It needs board class plus high-card/overcard quality (and sometimes BDFD) to be reliable.

Backdoor-only hands simplify in the opposite direction: BDFD/BDSD without a direct draw are overwhelmingly folds against 75%.

## Strong made hands

| Hand | ABx | Axx | BBx | Kxx | [Q-8]x | [7-4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Set / Trips** | R | C | R | R | R | C |
| **Two pair** | R | C | C | C | C | C |
| **Straight** | C | R | R | — | R | R |

Evidence for the pure simplifications (mean EV loss of chosen action):

- ABx: set R 0.011bb; two pair R 0.009bb; straight C 0.001bb.
- Axx: set C 0.019bb; two pair C 0.008bb; straight R 0.024bb.
- BBx: set R 0.011bb; two pair C 0.008bb; straight R 0.014bb.
- Kxx: set R 0.016bb; two pair C 0.006bb.
- [Q-8]x: set R and C are close (~0.022bb each), use R; two pair C ~0.020bb; straight R 0.016bb.
- [7-4]x: set C 0.008bb; two pair C 0.003bb; straight R 0.036bb.

## One-pair strategy

### Overpair / top pair

**Call everywhere** is robust. Overall pure-call EV loss is about 0.001bb for overpairs and 0.003bb for top pair.

### High underpair

- ABx: **Fold**.
- BBx, Kxx, [Q-8]x, [7-4]x: **Call** is the practical default.
- Axx needs an explicit pocket-rank threshold:

| A-high board second card | Call high-underpair from |
|---|:---:|
| A9x | TT+ |
| A8x | TT+ |
| A7x | 99+ |
| A6x | 99+ |
| A5x | 88+ |
| A4x | 88+ |
| A3x | 88+ |

Lower underpairs above the second board card fold. A direct straight draw can override the fold and continue.

### Second pair

- ABx: **Call with A/K kicker, BDFD, or a direct straight draw; otherwise Fold.** No-draw second pair with Q-or-worse kicker is predominantly fold and the fold simplification is near the 0.02bb tolerance.
- BBx: **Call with T+ kicker or BDFD/direct draw; Fold with 9-or-lower kicker and no useful draw/backdoor.**
- Axx, Kxx, [Q-8]x, [7-4]x: **Call** is the base rule.

### Third pair

- ABx: **Fold by default**. Gutshot without BDFD can Call; gutshot+BDFD is raise-heavy and can Raise.
- Axx: **Fold naked; Call with BDFD; direct gutshot/OESD continues aggressively (Raise is a good simple action for the direct-draw subgroups).**
- BBx: **Fold by default; Call with BDFD or OESD.** A naked gutshot does not automatically rescue the hand.
- Kxx, [Q-8]x, [7-4]x: **Call** is the practical base rule.

### Weak pocket pair

This category changes the most from the 33% solution.

Against 75%, **Fold is the default on every board class**:

- ABx: ~99.8% fold.
- Axx: ~97.2% fold overall.
- BBx: ~98.7% fold.
- Kxx: ~94.6% fold.
- [Q-8]x: ~92.5% fold.

Low `[7-4]x` is more mixed, but the class has little weight and is not worth a large rule tree. Practical exceptions worth keeping:

- weak pocket pair + OESD: **Call** on BBx / [Q-8]x / low boards;
- weak pocket pair + gutshot: **Call** on low Axx/low-board structures when the gutshot is real and connected;
- otherwise **Fold**.

## High-card direct draws

### OESD (no made pair)

| Draw | ABx | Axx | BBx | Kxx | [Q-8]x | [7-4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **OESD** | C | R | C | R | R | R* |

`*` On low boards OESD+BDFD is very close between C/R; pure Call is also acceptable. The useful human default is still Raise for the naked OESD.

This is a major change from the 33% strategy, where pure Raise was a good universal OESD simplification.

### Gutshot (no made pair)

Gutshots are the main category that cannot be reduced to one universal action without meaningful EV loss.

A practical compact rule set is:

- **ABx:** naked gutshot -> Fold; with BDFD -> Call as a simplification. Exact KJ/KQ gutshots are the main continue exceptions.
- **Axx:** Call.
- **BBx:** Ace-high gutshot -> Call; Ace-high gutshot+BDFD -> Raise; weaker gutshots -> Fold.
- **Kxx:** Call; BDFD can shift some combos toward Raise, but Call remains an acceptable simplification.
- **[Q-8]x:** AK/KQ/KJ gutshots -> Call; weaker Ace-high gutshots (AQ/AJ/AT in the relevant no-pair structures) often Fold; BDFD makes many K-high gutshots raise-heavy.
- **[7-4]x:** no clean universal action. Strong two-overcard gutshots prefer Call, while lower gutshots become more raise-heavy; gutshot+BDFD tends toward Call. This is the one residual class where an exact-rank rule would be needed for a tighter solver approximation.

For a simple live/grind strategy, it is better to accept some EV approximation in `[7-4]x` gutshots than add a large decision tree.

## High cards without a direct draw

The generic backdoor categories mostly disappear against 75%:

- BDFD only -> **Fold**.
- BDSD only -> **Fold**.
- BDFD+BDSD only -> **Fold**.
- Air -> **Fold**.

Exact broadway exceptions worth remembering:

- `[Q-8]x`: bare **AK Call**, bare **AQ Call**, bare **AJ Fold**; AJ with BDFD can Call.
- `[7-4]x`: bare **AK Call**, bare **AQ Call**, bare **AJ Fold** (AJ is close enough to fold under the 0.02bb simplification threshold); AJ with BDFD+BDSD can Call.
- `Kxx`: bare AQ is normally Fold, but AQ with BDFD+BDSD becomes a Call.

## Human-playable base matrix (75%)

This is the table to learn first; the notes below it are the only important modifiers.

| Hand category | ABx | Axx | BBx | Kxx | [Q-8]x | [7-4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Set / Trips** | R | C | R | R | R | C |
| **Two pair** | R | C | C | C | C | C |
| **Straight** | C | R | R | — | R | R |
| **Overpair / Top pair** | C | C | C | C | C | C |
| **High underpair** | F | threshold | C | C | C | C |
| **Second pair** | conditional | C | conditional | C | C | C |
| **Third pair** | F* | F* | F* | C | C | C |
| **Weak pocket pair** | F | F | F | F | F | F* |
| **OESD (high card)** | C | R | C | R | R | R |
| **Gutshot (high card)** | F/C* | C | F/C/R* | C | rank-dependent | rank-dependent |
| **Bare AK / AQ, no direct draw** | — | — | — | F* | C | C |
| **BDFD / BDSD only / Air** | F | F | F | F | F | F |

Important modifiers:

1. Axx high-underpair uses the explicit TT/99/88 threshold table above.
2. ABx second pair: C with A/K kicker or BDFD/direct draw; otherwise F.
3. BBx second pair: C with T+ kicker or BDFD/direct draw; weak no-draw kicker F.
4. Third-pair direct draws/backdoors can override the base F on ABx/Axx/BBx as described above.
5. Weak pocket pair stays F unless it has a sufficiently real direct straight draw; low-board exceptions exist but are not worth a large default rule tree.
6. Generic backdoor equity is not enough to continue against 75%.

## Main strategic change from 33% to 75%

The large c-bet does not merely tighten the same 33% strategy. It changes which properties matter:

- made-hand strength matters much more (second/third pair split becomes necessary);
- weak pocket pairs collapse toward fold almost everywhere;
- backdoor-only high cards collapse toward fold;
- OESD action becomes board-dependent;
- gutshots become the main complex bluff-catcher/semi-bluff family and need high-card quality, not just the label `gutshot`;
- value hands slow-play more selectively, so `Set/Two pair` can no longer be one category.

Scope: this report is only RNG001 / BRD001 (unpaired rainbow flops) against CFG002 UTG 75% c-bet.
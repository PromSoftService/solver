# CFG002 refined human categories (BB vs UTG 75% c-bet)

Source: RNG001 / CFG002 / BRD001, 106381 combo rows, 286 canonical unpaired rainbow flops. Practical simplification tolerance is 0.02bb where possible, but human-playability is allowed to override exact solver mixing.

Board classes are restored to the original study taxonomy:

- `A[K-J]x`
- `A[T-2]x`
- `BBx`
- `K[9-2]x`
- `[Q-8]x`
- `[7-4]x`

## Pair + straight-draw findings

### Pair + OESD

Where this structure exists in meaningful weight, Call is the robust common simplification across pair types.

- BBx, all pair+OESD: F 10.1 / C 67.3 / R 22.6; pure-C mean loss 0.0109bb.
- [Q-8]x, all pair+OESD: F 0.0 / C 66.2 / R 33.8; pure-C mean loss 0.0035bb.
- [7-4]x, all pair+OESD: F 0.0 / C 78.0 / R 22.0; pure-C mean loss 0.0050bb.

This includes overpair, high underpair, top pair, second pair, third pair, and weak pocket-pair subgroups where present. Therefore the practical rule is:

**Any pair + OESD -> Call.**

### Pair + Gutshot

For all ordinary made-pair types (overpair/high underpair/top/second/third pair), Call is the useful common simplification. The important exception is weak pocket pairs.

Practical rule:

**Any non-weak-pocket pair + Gutshot -> Call.**

Weak pocket pair + Gutshot remains separate:

- A[K-J]x -> Fold.
- A[T-2]x -> Call.
- BBx -> Fold.
- K[9-2]x -> no meaningful standalone population in this dataset.
- [Q-8]x -> Fold as the simple rule.
- [7-4]x -> Call.

Weak pocket pair + OESD -> Call where it exists.

## Second pair simplification

Kicker split is not worth keeping. Draw structure matters more.

- A[K-J]x plain second pair: Fold is the useful simplification (pure-F mean loss ~0.025bb vs pure-C ~0.114bb).
- A[K-J]x second pair + BDFD: Call.
- A[K-J]x second pair + Gutshot: Call.
- A[T-2]x and all lower board classes: Call is the base rule.

Therefore:

**Second pair -> Call everywhere, except naked/no-useful-backdoor second pair on A[K-J]x -> Fold.**

No kicker category is required.

## Third pair simplification

- Naked third pair: Fold on A[K-J]x, A[T-2]x and BBx; Call on K[9-2]x and lower.
- Third pair + BDFD: Fold on A[K-J]x; Call on A[T-2]x and lower.
- Third pair + Gutshot/OESD: Call everywhere as the human simplification.

## Two overcards first, draws as modifiers

Treat `2 overcards` as the base category and then inspect modifiers.

### 2 overcards, no direct straight draw

- [Q-8]x plain -> Fold.
- [Q-8]x + BDFD -> Call.
- [7-4]x plain -> Fold.
- [7-4]x + BDFD -> Fold.

On BBx, two-overcard high-card hands in the current range naturally come with a direct straight draw, so there is no useful plain two-overcard bucket.

### 2 overcards + Gutshot

Call is the clean universal simplification on BBx, [Q-8]x and [7-4]x, with or without BDFD.

**2 overcards + Gutshot -> Call.**

### 2 overcards + OESD

Call is chosen as the human simplification. It is excellent on BBx/[Q-8]x. On low boards solver can prefer Raise in some naked-OESD subsets, but forcing Call keeps the overcard rule simple and the extra EV cost is accepted.

**2 overcards + OESD -> Call.**

## No-pair gutshot after overcard precedence

After first checking for 2 overcards:

- A[K-J]x -> Fold.
- A[T-2]x -> Call.
- BBx -> Fold.
- K[9-2]x -> Call.
- [Q-8]x -> Call.
- [7-4]x -> Call.

No check-raise is required for the human gutshot strategy. This deliberately gives up some solver EV in selected suited/low-board combinations to remove a large decision tree.

## Refined human matrix

| Hand category | A[K-J]x | A[T-2]x | BBx | K[9-2]x | [Q-8]x | [7-4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Set / Trips | R | R | R | R | R | C |
| Two pair | R | C | C | C | C | C |
| Straight | C | R | R | — | R | R |
| Overpair / Top pair | C | C | C | C | C | C |
| High underpair | F/C* | F/C* | C | C | C | C |
| Second pair, naked | F | C | C | C | C | C |
| Second pair + BDFD | C | C | C | C | C | C |
| Third pair, naked | F | F | F | C | C | C |
| Third pair + BDFD | F | C | C | C | C | C |
| Any non-weak-pocket pair + Gutshot | C | C | C | C | C | C |
| Any pair + OESD | C | C | C | C | C | C |
| Weak pocket pair, naked | F | F | F | F | F | F |
| Weak pocket pair + Gutshot | F | C | F | — | F | C |
| Weak pocket pair + OESD | — | — | C | — | C | C |
| 2 overcards, plain | — | — | — | — | F | F |
| 2 overcards + BDFD only | — | — | — | — | C | F |
| 2 overcards + Gutshot | — | — | C | — | C | C |
| 2 overcards + OESD | — | — | C | — | C | C |
| Gutshot, <2 overcards | F | C | F | C | C | C |
| BDFD/BDSD only / Air | F | F | F | F | F | F |

`F/C*` for high underpairs means: closer to the middle board rank -> Fold; closer to the top board rank -> Call. On A[T-2]x the dataset shows a particularly clean practical transition: one rank above the middle card is mostly Fold, two or more ranks above it shifts toward Call.

Precedence for human play:

1. Made straight / set / two pair.
2. Pair + OESD or pair + Gutshot modifiers.
3. Top/second/third/high-underpair base rule.
4. Weak pocket pair special rules.
5. Two overcards, then inspect OESD/Gutshot/BDFD modifier.
6. Remaining no-pair OESD/gutshot.
7. Backdoor-only / air -> Fold.

# CFG001 refined human categories — BB vs UTG B33

Source dataset: `datasets/DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv`.

Spot: UTG open 2.5bb, BB call; flop BB check, UTG bets 1/3 pot; simplify BB response. Board classes are the established six classes: `A[K-J]x`, `A[T-2]x`, `BBx`, `K[9-2]x`, `[Q-8]x`, `[7-4]x`.

The aim is a human-executable strategy with clean transitions. Small local EV losses are accepted to remove oscillating rules.

## Recommended matrix

| Категория руки | A[K–J]x | A[T–2]x | BBx | K[9–2]x | [Q–8]x | [7–4]x |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Two pair+** | **R** | **R** | **R** | **R** | **R** | **R** |
| **Любая пара** | **C** | **C** | **C** | **C** | **C** | **C** |
| **Weak pair** | **F** | **C** | **C** | **C** | **C** | **C** |
| **OESD** | **R** | **R** | **R** | **R** | **R** | **R** |
| **Gutshot + БДФД** | **R** | **R** | **R** | **R** | **R** | **R** |
| **2 overcards + дро** | — | — | **C** | — | **C** | **C** |
| **Голый Gutshot** | **C** | **C** | **C** | **C** | **C** | **C** |
| **Голые AK / AQ / AJ** | — | — | — | **C** | **C** | **C** |
| **2 overcards** | — | — | — | — | **C** | **F** |
| **Air** | **F** | **F** | **F** | **F** | **F** | **F** |

Precedence for overlapping descriptions:

1. Made hand first: `Two pair+`, then any ordinary pair, then `Weak pair`.
2. For no-pair hands, `2 overcards + дро` overrides the generic `OESD` / `Gutshot + БДФД` rows.
3. `Голые AK / AQ / AJ` means no made pair and no direct/backdoor draw already covered above.
4. `2 overcards` means no draw and no stronger ace-high exception.
5. `Air` is the remainder.

For `2 overcards + дро`, `дро` is intentionally broad: BDFD, BDSD, Gutshot, or OESD. This removes separate `2 overcards + BDFD` and `2 overcards + Gutshot` rows.

## Key EV checks

All losses below are reach-weighted loss from forcing the stated pure action versus the best pure action in the dataset, in bb.

### Weak pair simplification

The clean rule `F only on A[K-J]x, C everywhere else` removes the old `F / F-C / F / C / C / C` oscillation.

- `A[K-J]x -> F`: 0.0064bb.
- `A[T-2]x -> C`: 0.0574bb.
- `BBx -> C`: 0.0666bb; forcing Fold is 0.0617bb, so C vs F is nearly indifferent at the coarse-category level.
- `K[9-2]x -> C`: 0.0001bb.
- `[Q-8]x -> C`: 0.0003bb.
- `[7-4]x -> C`: 0.0022bb.

### 2 overcards + draw -> Call

The useful-draw merge (BDFD/Gutshot/OESD) has Call losses:

- `BBx`: 0.0068bb.
- `[Q-8]x`: 0.0096bb.
- `[7-4]x`: 0.0132bb.
- all these boards combined: 0.0098bb.

Adding BDSD-only two-overcard hands to the same row keeps the merge practical:

- `BBx`: 0.0068bb.
- `[Q-8]x`: about 0.0153bb.
- `[7-4]x`: about 0.0302bb.
- all combined: about 0.0164bb.

This is why the broad `2 overcards + дро -> C` row is preferred.

### Bare strong ace-high merge

Merging bare `AK/AQ/AJ` into one Call row gives:

- `K[9-2]x`: 0.0228bb.
- `[Q-8]x`: 0.0041bb.
- `[7-4]x`: 0.0032bb.
- combined: about 0.0086bb.

The old special case `AJ -> F` on K-high boards is therefore removed for simplicity.

### OESD -> Raise

High-card/no-pair OESD forced Raise losses by board class:

- `A[K-J]x`: 0.0079bb.
- `A[T-2]x`: 0.0014bb.
- `BBx`: 0.0118bb.
- `K[9-2]x`: 0.0037bb.
- `[Q-8]x`: 0.0063bb.
- `[7-4]x`: 0.0129bb.

This is an excellent universal bluff-raise row.

### Naked Gutshot -> Call

High-card/no-pair Gutshot without BDFD forced Call losses:

- `A[K-J]x`: 0.0244bb.
- `A[T-2]x`: 0.0072bb.
- `BBx`: 0.0311bb.
- `K[9-2]x`: 0.0038bb.
- `[Q-8]x`: 0.0147bb.
- `[7-4]x`: 0.0106bb.

The two slightly-above-0.02 classes are accepted to preserve one universal `Gutshot -> C` rule.

## Relationship to the 3/4-pot table

Rows such as `Third pair + BDFD` and `Pair + Gutshot` are not needed separately against the 1/3 c-bet: the broader `Любая пара -> C` rule already subsumes them. The genuinely missing high-card category was `2 overcards + Gutshot`; it is best handled by merging it together with `2 overcards + BDFD`, OESD and BDSD into `2 overcards + дро -> C`.

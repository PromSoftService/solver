# CFG001 — bare 2 overcards fold simplification

Source dataset: `datasets/DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv`.

Question: after keeping `2 overcards + draw` as a separate continue category and keeping bare `AK/AQ/AJ` as a separate strong ace-high continue category, can the remaining bare two-overcard hands always Fold?

Definition of the tested residual category: `High card`, exactly two overcards to the flop, no OESD/Gutshot, no BDFD, no BDSD, and hole rank class not `AK`, `AQ`, or `AJ`.

| Board class | Solver F/C/R | Loss if forced Fold | Loss if forced Call |
|---|---:|---:|---:|
| `[Q-8]x` | 66.0 / 33.8 / 0.2 | **0.0109bb** | 0.0220bb |
| `[7-4]x` | 79.9 / 20.0 / 0.1 | **0.0093bb** | 0.0767bb |
| **Combined** | 74.0 / 25.8 / 0.2 | **0.0100bb** | 0.0536bb |

There are no useful residual bare-two-overcard buckets in the other established board classes under this classification: on BBx the relevant two-overcard hands naturally carry a direct straight draw and are therefore handled by `2 overcards + draw`; on Ace-high/K-high boards two overcards are structurally unavailable.

Conclusion: **yes — the residual `2 overcards` row can be Fold everywhere** at negligible cost, provided the precedence remains:

1. `2 overcards + draw` -> Call.
2. bare `AK/AQ/AJ` -> Call where applicable.
3. remaining bare `2 overcards` -> Fold.

For comparison, folding *all* bare two-overcard hands without preserving the `AK/AQ/AJ` exception is bad: combined forced-Fold loss is about 0.1707bb, driven by strong ace-high hands on `[Q-8]x`.

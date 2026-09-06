# CFG002 — requested human simplification losses

Source: `DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv`, 106381 combo rows. Reach-weighted action-loss values are measured relative to the best pure action in the dataset. Practical reference tolerance: 0.02bb.

Requested simplifications evaluated:

- Second pair -> Call everywhere.
- Third pair + BDFD (no direct straight draw) -> Fold on A[K-J]x, A[T-2]x, BBx.
- Weak pocket pair -> Fold regardless of draw.
- All normal pair + Gutshot -> Call; normal pair means Overpair, High underpair, Top pair, Second pair, Third pair, excluding Weak pocket pair.
- 2 overcards + any draw -> one broad Call category. Here `draw` means BDFD and/or Gutshot/OESD.

## Results

| Simplification | Chosen action | Reach-weighted mean loss |
|---|:---:|---:|
| Second pair, all boards | C | 0.0255bb |
| Third pair + BDFD, first 3 high classes, no direct draw | F | 0.2093bb |
| Weak pocket pair, all variants | F | 0.0092bb |
| Normal pair + Gutshot, all boards | C | 0.0200bb |
| 2 overcards + BDFD or Gutshot only | C | 0.0923bb |
| 2 overcards + any draw, including OESD | C | 0.0800bb |

Second pair by board class, if always Call:

- A[K-J]x: 0.0776bb
- A[T-2]x: 0.0198bb
- BBx: 0.0247bb
- K[9-2]x: 0.0065bb
- [Q-8]x: 0.0061bb
- [7-4]x: 0.0077bb

Third pair + BDFD, no direct straight draw, if forced Fold:

- A[K-J]x: 0.0126bb
- A[T-2]x: 0.2230bb
- BBx: 0.3095bb

This shows that Fold is a good simplification only on A[K-J]x. On A[T-2]x and BBx, Call is much better.

Normal pair + Gutshot, if always Call:

- A[K-J]x: 0.0073bb
- A[T-2]x: 0.0509bb
- BBx: 0.0377bb
- [Q-8]x: 0.0069bb
- [7-4]x: 0.0030bb
- all boards combined: 0.0200bb

2 overcards + any draw, if always Call:

- BBx: 0.0023bb
- [Q-8]x: 0.0412bb
- [7-4]x: 0.2659bb
- all boards combined: 0.0800bb

The broad overcards+draw category is heterogeneous on very low boards, but it is relatively rare. Across all BB decision states, the requested changed categories together cover 27.4% of reach weight. Their chosen simple actions have an average loss of 0.0329bb within that affected subset and contribute about 0.0090bb of reach-weighted EV loss per BB decision across the full range.

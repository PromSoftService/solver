# STU002 clustering comparison

This report compares coarser hand-category vocabularies against the current
47-category simplified policy.  Every candidate is rebuilt from the source
combo rows with the same frequency rule (pure above 65%, otherwise a strict
50/50 top-two mix), and then audited with reach-weighted local regret.

## Recommended common vocabulary (13 categories)

- Collapse every made-hand base completely: Two pair+, Overpair, Top pair,
  Second pair, Third pair, Underpair, and Weak pair.  BDFD, Gutshot, and OESD
  do not appear in their displayed labels.
- Split 2 overcards into `2 overcards` and `2 overcards + draw`, where draw
  means BDFD or a direct straight draw.
- Split A-high into `A-high` and `A-high + direct draw`.  Ignore BDFD here and
  merge Gutshot/OESD into the direct-draw row.
- Split Air into `Air` and `Air + direct draw`.  Ignore BDFD here and merge
  Gutshot/OESD into the direct-draw row.

This keeps one vocabulary across all six decision tables.  It has 13 displayed
hand categories instead of 47.

## Loss comparison

The values below are root-normalized local regret.  The sum across branches is
an additive local-regret diagnostic, not adaptive exploitability.

| Model | Categories | Sum loss, bb/100 | Extra vs 47 categories, bb/100 |
|---|---:|---:|---:|
| Current strict simplification | 47 | 1.1339 | 0.0000 |
| Made hands collapsed only | 25 | 1.4262 | 0.2923 |
| Recommended common vocabulary | 13 | 1.5639 | 0.4300 |
| Naive `base / base + any draw` vocabulary | 13 | 8.1099 | 6.9761 |

The made-hand merge is a good complexity/loss tradeoff.  Its largest branch
increment is 0.1807 bb/100 at `03_BB_AFTER_CBET`; the total increment across
all six decision points is 0.2923 bb/100.

## Why BDFD cannot always mean `+ draw`

The naive 13-row version groups BDFD, Gutshot, and OESD together for every
unmade base.  It fails primarily in BB defence after the c-bet:

- grouping all modified Air as `Air + draw` adds 5.3489 bb/100 at the root;
- keeping direct straight-draw information while ignoring the BDFD flag adds
  only 0.0215 bb/100;
- the same direction appears for A-high: a lone BDFD behaves more like plain
  A-high than like a direct straight draw;
- for 2 overcards the opposite binary split works better: a BDFD can join the
  direct draws in `2 overcards + draw`.

Therefore the displayed clustering should depend on both the base category
and the type of modifier.  It should not use a universal definition of
`+ draw` for every base.

Small negative deltas in the machine-readable comparison are possible because
merging changes the frequency average and can move a cell across the 65%
pure/mix threshold; they are not evidence that information itself has value.

Full candidate results are stored in `cluster-comparison.json`.

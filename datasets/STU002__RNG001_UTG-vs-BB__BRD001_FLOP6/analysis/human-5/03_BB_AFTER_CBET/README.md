# STU002 BB response: five-class human candidate

This is a separate, locally EV-audited candidate. It does not replace the canonical
ten-class workbook and is not a re-solve or an exploitability proof.

| Hand category | ABB | Axx | BBB | Bxx | [9-2]xx |
|---|---:|---:|---:|---:|---:|
| Two pair+ | C/R | R/C | C/R | R | R/C |
| Overpair | — | — | — | C/R | C |
| Top pair | C | C | BDFD | C | C/R |
| Underpair | — | C | — | C | C |
| Second pair | F | C | F | C/R | C |
| Weak pair | — | F | — | C/F | C |
| Third pair | F | C/F | F | C | C |
| Low pocket pair | F | F | F | F | F |
| OESD | R/C | R | C | R/C | R/C |
| Gutshot | C/F | C | C/F | C/R | C |
| 2 overcards + BDFD | — | — | — | C/R | C/F |
| Air | F | F | F | C/F | C/F |

## Selectors

- **Top pair / BBB:** CALL with BDFD; otherwise FOLD.
- **Weak pair / Bxx:** CALL when the flop has one Broadway card; FOLD when it has two.
- **Third pair / Axx:** CALL on A + two low cards; on A + Broadway + low CALL only with BDFD.
- **Gutshot / ABB:** CALL with any made pair inside the Gutshot; otherwise FOLD.
- **Gutshot / BBB:** CALL with top, second or third pair inside the Gutshot; otherwise FOLD.
- **2 overcards + BDFD / [9-2]xx:** CALL with Ax or two Broadway hole cards; otherwise FOLD.
- **Air / Bxx and [9-2]xx:** CALL only AK; otherwise FOLD.

## Audit summary

- Solver F/C/R: 47.90% / 39.09% / 13.01%.
- Candidate F/C/R: 49.09% / 39.27% / 11.65%.
- Mean loss versus source mix: 0.008601 bb.
- Mean oracle regret: 0.010608 bb.
- Weighted P95 / P99: 0.031112 / 0.234361 bb.

`C/R` and `R/C` are the same exact 50/50 randomizer; order records solver majority.
`C/F` is deterministic and uses the stated selector, never a randomizer.

# Research history before the full-tree reset

## Why the repository was reset on 2026-09-08

The first research cycle successfully automated TexasSolverGPU and produced seven flop-node datasets, but later review exposed a methodological problem in the study definitions.

The old setup used separate trees for UTG-vs-BB B33 and B75:

- CFG001 allowed only B33 at the studied UTG flop bet node;
- CFG002 replaced that single size with B75.

That means the UTG range arriving in the B75 branch was optimized in a world where B33 did not exist, and vice versa. Those are not the same branch ranges that arise when B33 and B75 compete inside one solved tree. Therefore the old B33/B75 defense datasets must not be treated as two branches of one real strategy.

The old runner also solved the same tree repeatedly to export different decision nodes. TexasSolverGPU solves the configured game tree, while the runner was storing only one selected node. That discarded information needed for later turn/river analysis and wasted GPU time.

## What remains useful from the old cycle

The cycle established several reliable engineering facts:

- `TexasSolverGpu_131.exe` can be automated headlessly through its WebView2 bridge;
- multiple bet sizes are accepted by the native config as a comma-separated sizing list;
- the bridge can initialize, allocate, solve, poll status, apply history and export strategy data;
- `RNG001` and `BRD001` definitions were audited;
- board isolation/retry and manifesting are useful production patterns;
- `loss_if_action` is local regret against the solved opponent strategy, not adaptive exploitability.

It also established a poker-research lesson: aggregate EV/frequency objectives can produce ugly human policies if compression is attempted before preserving the correct underlying solved tree.

## Historical locations

Immediately before reset, remote main was:

`bec0b758fe7957a45d028f1adaa2a5252ff0598a`

That Git history contains:

- old CFG001/CFG002/CFG003 configs;
- all seven old datasets;
- old analysis reports;
- universal strategy EXP-001 through EXP-004;
- runner v015 decision-node exporters.

They are intentionally absent from current `main` so a new study cannot accidentally mix old and new evidence.

## New rule

**Solve once, export the complete postflop strategy tree, analyze later.**

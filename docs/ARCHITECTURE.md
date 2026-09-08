# Full-tree runner architecture

## Objective

For each registered flop board, TexasSolverGPU must perform exactly one equilibrium solve of the complete configured postflop abstraction. The result must preserve enough native strategy-tree information to analyze arbitrary flop, turn and river nodes later without another GPU solve.

## Tree versus report

A solver tree and an analytical report are different objects.

The tree contains all actions available to both players and all chance runouts. A report is a later projection of that tree, such as:

- UTG root c-bet frequencies;
- BB response after UTG B33;
- turn probe after a specific flop line and turn card;
- river defense after a specific runout.

Reports must never define the tree. A report may filter to B33, but B75 remains present in the solved tree if B75 was an allowed action.

## Full-tree export contract

Per board, a successful worker creates:

- `run.json` — solver/runtime/status/export metadata;
- `tree.json.gz` or chunked `tree.json.gz.partNNN` — complete native strategy dump;
- `tree.meta.json` — compression/chunking/hash/validation metadata;
- `bridge-transcript.jsonl` — compact API audit trail;
- optional `frontend-export-hints.json` only when full export discovery fails.

A full-tree export is accepted only if validation finds strategy/action nodes on flop, turn and river in the exported JSON. If only the current street is present, the board run fails.

The GPU v0.2.0 public repository ships a Python strategy viewer that expects a nested JSON game tree with `childrens`, chance nodes and strategy payloads. The older open-source TexasSolver line also exposes full strategy dumps. The production worker probes the GPU bridge for the corresponding full export and keeps the known `export.currentStreet` endpoint only as a diagnostic fallback; a current-street-only payload cannot satisfy the full-tree contract.

## Storage

Transient solves live under ignored `output/`. Only a completely validated study is promoted to `results/`.

Large gzip exports are split into Git-safe chunks below the GitHub single-file limit. `tree.meta.json` records ordered parts and SHA-256 of the complete gzip stream so analysis code can reconstruct it deterministically.

## Study transaction

A study launcher behaves like a transaction:

1. fetch remote and require local HEAD == `origin/main`;
2. require clean tracked/untracked working state (ignored output is allowed);
3. materialize the effective native config;
4. run all boards under `output/`;
5. verify zero failed boards and all full-tree artifacts;
6. add exact inputs + run manifest;
7. atomically move run directory to `results/`;
8. `git add` only that result directory;
9. commit;
10. `git pull --rebase origin main`;
11. push `main`.

No result commit is created on partial failure.

## STU001 abstraction

STU001 intentionally starts with a compact but expressive tree:

- open bets, flop: 33%, 75%, all-in;
- open bets, turn: 33%, 75%, all-in;
- open bets, river: 33%, 75%, 150%, all-in;
- normal raise: native TexasSolver `60% pot-raise` parameter;
- all-in raise is also enabled;
- one normal raise maximum per street;
- OOP turn/river donk: 33%, 75% (plus 150% river), all-in.

Why no 50% or 100% normal bet in the baseline: the project goal is ultimately a small human strategy. B33 and B75 cover small/large normal betting; B150 preserves a genuinely different river overbet regime. Additional sizes can be introduced later only as a new study version if evidence shows they are necessary.

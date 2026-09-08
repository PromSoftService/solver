# Full-tree runner architecture

## Objective

For each registered flop board, TexasSolverGPU performs exactly one equilibrium solve of the complete configured postflop abstraction. The result must preserve enough native strategy-tree information to analyze arbitrary flop, turn and river nodes later without another GPU solve.

## Tree versus report

A solver tree and an analytical report are different objects.

The tree contains all actions available in that study and all chance runouts. A report is a later projection of that saved tree, such as:

- UTG flop c-bet frequencies;
- BB response after UTG B33;
- turn strategy after a specific flop line and turn card;
- river defense after a specific runout.

Reports must never redefine the tree. GPU solving and analytical filtering are separate stages.

## Full-tree export contract

Per board, a successful worker creates:

- `run.json` — solver/runtime/status/export metadata;
- `tree.json.gz` or chunked `tree.json.gz.partNNN` — complete native strategy dump;
- `tree.meta.json` — compression/chunking/hash/validation metadata;
- `bridge-transcript.jsonl` — compact API audit trail;
- `export-probes.json` — attempted full-tree export methods and structural results.

A full-tree export is accepted only if validation finds nested strategy/action/chance structure including turn and river strategy nodes. A current-street-only or selected-node-only payload is not a successful study result.

The proven v015 startup/init/allocate/solve/poll/window-suppression path remains the base. The only mandatory architectural change from the old studies is post-solve export: preserve the complete solved postflop tree rather than exporting one decision node.

If no probed bridge export yields a validated complete tree, the worker throws `FULL_TREE_EXPORT_UNRESOLVED`; the batch stops immediately and preserves diagnostics. Do not silently downgrade to node-only data.

## Storage

Transient solves live under ignored `output/`. Only a completely validated study is promoted to `results/`.

Large gzip exports are split into Git-safe chunks below the GitHub single-file limit. `tree.meta.json` records ordered parts and SHA-256 of the complete gzip stream so analysis can reconstruct it deterministically.

## Study transaction

A study launcher behaves like a transaction:

1. fetch remote and require local HEAD == `origin/main`;
2. require clean tracked/untracked working state;
3. materialize the exact native config for the registered study;
4. run the requested boards under `output/`;
5. verify zero failed boards and all full-tree artifacts;
6. add exact inputs + run manifest;
7. move the completed run to `results/`;
8. `git add` only that result directory;
9. commit;
10. `git pull --rebase origin main`;
11. push `main`.

No result commit is created on partial failure.

## Active STU002 abstraction

STU002 deliberately uses the historical CFG001 poker tree because the larger multi-sizing STU001 tree proved too slow for the practical batch workflow.

Exact settings:

- flop OOP/BB open bet: none;
- flop IP/UTG bet: 33%;
- flop OOP/BB raise parameter: 60;
- flop IP/UTG raise parameter: 100;
- turn OOP/IP bet: 100%;
- turn OOP donk: 100%;
- turn OOP/IP raise: 100%;
- river OOP/IP bet: 100%;
- river OOP donk: 100%;
- river OOP/IP raise: 100%;
- `maxRaiseNumber = 3`;
- study `addAllinThreshold = 200`, converted by the worker to native `2.0`;
- add-all-in flags enabled for both players on all streets, matching old CFG001.

Source of truth for these action settings: historical commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`, CFG001.

This does **not** reactivate the historical node-only datasets. Only the old tree abstraction is reused; new results must satisfy the full-tree export contract.

## Inactive STU001

STU001 remains registered as the larger B33/B75/B150 full-tree experiment. It is preserved for provenance but is not the active study because of solve time.

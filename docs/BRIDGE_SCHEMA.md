# Native bridge schema — TexasSolverGPU v0.2.0 `_131`

This document separates **verified bridge behavior** from the full-tree export method that still has to be confirmed against the user's installed GPU runtime.

## Verified bridge envelope

Initial request:

```json
{"id":"rpc_1","method":"bridge.ping","params":{}}
```

Authenticated requests carry:

```json
{
  "id":"rpc_2",
  "method":"solver.solve.status",
  "params":{
    "apiBase":"http://127.0.0.1:6006",
    "path":"/api/solve/status",
    "method":"GET",
    "bridge_token":"<token from bridge.ping>"
  }
}
```

For bodyless GET requests the `body` property must be **omitted**, not sent as `null`. This distinction was verified against v0.2.0.

## Verified methods used by the proven v015 base

| Native method | Compatibility path | HTTP verb |
|---|---|---|
| `solver.init` | `/api/init` | POST |
| `solver.allocate` | `/api/allocate` | POST |
| `solver.solve.start` | `/api/gpu-solve` | POST |
| `solver.solve.status` | `/api/solve/status` | GET |
| `solver.solve.stop` | `/api/solve/stop` | POST |
| `solver.history.apply` | `/api/apply-history` | POST |
| `solver.node.actionsAfter` | `/api/actions-after` | POST |
| `solver.export.currentStreet` | `/api/export/current-street` | POST |

The production v020 worker is deliberately rebuilt from the proven v015 startup/init/allocate/solve/poll/window-suppression implementation. Only the post-solve export stage changed materially.

## Multiple sizing strings

The runner normalizes sizing fields as comma-separated percentage tokens. For example:

```text
33,75
```

becomes the native sizing string:

```text
33%,75%
```

This lets B33 and B75 coexist in the **same solved tree**. Do not return to separate B33-only and B75-only solves for branches that are supposed to compete at one node.

## STU001 effective tree settings

The active study materializes these settings for both players where applicable:

```text
flop bet:        33%,75%
turn bet:        33%,75%
turn OOP donk:   33%,75%
river bet:       33%,75%,150%
river OOP donk:  33%,75%,150%
normal raise:    60% native pot-raise parameter
max normal raises per street: 1
all-in: enabled flop/turn/river for both players
add_allin_threshold: 20.0 native value (study JSON stores 2000 and worker divides by 100)
```

`raise=60` must not be described as a fixed exact `3x` raise-to size. The resulting multiple depends on the preceding pot and bet.

STU001 starts at the flop with fixed RNG001 ranges, native pot 55 and effective stack 975. Preflop is not solved.

## Full-tree export contract

`solver.export.currentStreet` is verified but is **not sufficient** if its payload contains only one street. The new study requires a nested strategy tree containing action/chance/strategy structure through turn and river.

The public TexasSolverGPU viewer consumes a nested JSON tree with fields such as:

- `childrens`;
- `valid_actions`;
- `strategy`;
- `betting round` values including turn (`2`) and river (`3`).

The exact GPU v0.2.0 bridge method for producing the viewer-compatible complete dump is not publicly documented. Therefore v020 probes candidate export methods only **after the equilibrium solve**, validates the returned JSON structurally, and accepts a board only when turn and river strategy nodes are present.

Every probe is recorded in:

```text
export-probes.json
bridge-transcript.jsonl
```

If no candidate succeeds, the worker throws:

```text
FULL_TREE_EXPORT_UNRESOLVED
```

The batch stops immediately on that error. This is an exporter-discovery failure, not a reason to change STU001's ranges/tree or to solve the remaining 285 boards blindly. Fix the exporter using the saved probe/transcript evidence and resume the same study.

## Successful per-board full-tree artifacts

A successful board contains:

```text
run.json
tree.meta.json
tree.json.gz
```

or, if the compressed tree exceeds the Git-safe part size:

```text
tree.json.gz.part001
tree.json.gz.part002
...
```

`tree.meta.json` records the complete gzip SHA-256, original compressed byte count, export method/path, structural validation flags, and ordered part names.

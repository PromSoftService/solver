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

The production full-tree worker is deliberately rebuilt from the proven v015 startup/init/allocate/solve/poll/window-suppression implementation. Only the post-solve export stage changed materially.

## Sizing strings

The worker normalizes bare numeric sizing tokens by appending `%` before sending the native config. Empty strings remain empty.

Example:

```text
33 -> 33%
100 -> 100%
"" -> ""
```

Native raise values must not be described as fixed raise-to multiples. In particular historical `oopFlopRaise=60` is the TexasSolver native raise parameter, not a universal exact `3x`.

## Active STU002 effective tree settings

STU002 intentionally restores the old CFG001 action abstraction exactly:

```text
flop OOP/BB open bet:  empty
flop IP/UTG bet:       33%
flop OOP/BB raise:     60%
flop IP/UTG raise:     100%
turn OOP/IP bet:       100%
turn OOP donk:         100%
turn OOP/IP raise:     100%
river OOP/IP bet:      100%
river OOP donk:        100%
river OOP/IP raise:    100%
maxRaiseNumber:        3
all-in flags:          enabled for both players on flop/turn/river
add_allin_threshold:   2.0 native value (study JSON stores 200 and worker divides by 100)
```

These values are copied from historical CFG001 at commit `bec0b758fe7957a45d028f1adaa2a5252ff0598a`.

STU002 starts at the flop with fixed RNG001 ranges, native pot 55 and effective stack 975. Preflop is not solved.

## Full-tree export contract

`solver.export.currentStreet` is verified but is **not sufficient** if its payload contains only one street. The active study requires a nested strategy tree containing action/chance/strategy structure through turn and river.

The public TexasSolverGPU viewer consumes a nested JSON tree with fields such as:

- `childrens`;
- `valid_actions`;
- `strategy`;
- `betting round` values including turn (`2`) and river (`3`).

The exact GPU v0.2.0 bridge method for producing the viewer-compatible complete dump is not publicly documented. Therefore the worker probes candidate full-tree export methods only **after the equilibrium solve**, structurally validates every returned JSON payload, and accepts a board only when turn and river strategy nodes are present.

Every probe is recorded in:

```text
export-probes.json
bridge-transcript.jsonl
```

If no candidate succeeds, the worker throws:

```text
FULL_TREE_EXPORT_UNRESOLVED
```

The batch stops immediately on that error. This is an exporter-discovery failure, not a reason to change STU002's poker tree or to solve the remaining boards blindly. Fix only the exporter using the saved probe/transcript evidence and resume the same study.

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

# Verified TexasSolverGPU v0.2.0 bridge facts

This file intentionally contains only behavior that was actually observed/proven in the runner work. It must not list guessed full-tree API names as if they exist.

## WebView2 envelope

The frontend communicates with the native host through `window.chrome.webview`.

Initial bridge discovery uses:

```json
{"id":"rpc_1","method":"bridge.ping","params":{}}
```

Authenticated requests carry an API base/path/method plus the returned bridge token.

A verified compatibility detail: for bodyless GET requests, the `body` property must be **omitted**, not sent as JSON `null`.

## Verified methods used by v015

| Native method | Compatibility path | Purpose |
|---|---|---|
| `bridge.ping` | bridge message | obtain bridge token |
| `solver.init` | `/api/init` | initialize ranges/tree/config |
| `solver.allocate` | `/api/allocate` | allocate solver memory |
| `solver.solve.start` | `/api/gpu-solve` | start GPU solve |
| `solver.solve.status` | `/api/solve/status` | poll solve status |
| `solver.solve.stop` | `/api/solve/stop` | stop a running solve |
| `solver.history.apply` | `/api/apply-history` | select a node by action history |
| `solver.node.actionsAfter` | `/api/actions-after` | inspect legal actions/history navigation |
| `solver.export.currentStreet` | `/api/export/current-street` | export the selected/current-street subtree/node data |

`solver.export.currentStreet` is proven. It is **not evidence that a complete solved-tree exporter has been implemented**.

## Current-street strategy payload

The proven export exposes action-node information including fields such as:

- `valid_actions`;
- `strategy.card_strings`;
- `strategy.reach_probs`;
- `strategy.strategy_probs`;
- `strategy.action_evs`;
- `strategy.evs`.

The v015 worker validates vector lengths against the action list before producing combo output.

## Native config facts

The runner passes 1326 OOP and IP combo weights, flop board ids, starting pot/effective stack, rake settings and street sizing strings into `solver.init`.

Bare numeric sizing tokens are normalized to percentage strings. Multiple sizing tokens can be represented in the config, but the clean baseline deliberately makes no claim about what future study abstraction should use.

All-in flags/threshold and raise-count settings are passed through from the config.

## Not verified / not baseline API

The following names appeared only in a discarded experimental probe and must **not** be treated as real methods without new evidence from the installed runtime/frontend:

```text
solver.export.fullTree
solver.export.allStreets
solver.export.fullStrategy
solver.export.strategy
solver.export.tree
solver.dump.strategy
solver.dump.result
```

The next runner-development task is to discover the actual complete-strategy persistence mechanism, not to add more guessed names.

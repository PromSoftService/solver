# Verified TexasSolverGPU v0.2.0 bridge facts

Only behavior proven from the installed frontend/runtime and Windows GPU runs is documented here. Guessed full-tree method names are not API.

## WebView2 envelope

The frontend communicates through `window.chrome.webview`. Initial discovery sends:

```json
{"id":"rpc_1","method":"bridge.ping","params":{}}
```

Authenticated requests include `apiBase`, `path`, HTTP `method`, and the returned `bridge_token`. A bodyless GET must omit the `body` property rather than send JSON `null`.

## Verified solver methods

| Native method | Compatibility method/path | Proven purpose |
|---|---|---|
| `bridge.ping` | bridge message | obtain bridge token |
| `solver.init` | `POST /api/init` | initialize ranges/tree/config |
| `solver.allocate` | `POST /api/allocate` | allocate solver memory |
| `solver.solve.start` | `POST /api/gpu-solve` | start the single GPU solve |
| `solver.solve.status` | `GET /api/solve/status` | poll solve status |
| `solver.solve.stop` | `POST /api/solve/stop` | stop a running solve |
| `solver.history.apply` | `POST /api/apply-history` | select an exact integer history |
| `solver.node.actionsAfter` | `POST /api/actions-after` | inspect action labels/indexes |
| `solver.cards.possible` | `GET /api/possible-cards` | return legal cards as a 52-bit mask |
| `solver.export.currentStreet` | `POST /api/export/current-street` | export the native subtree for one street |

The full-tree exporter uses only the last three navigation/export primitives after the solve is complete. It does not call another solve.

## Request/response schemas used for persistence

Apply history:

```json
{"history":[0,0,0]}
```

Possible cards response:

```json
{"possible_cards":2251799813685247}
```

Bit `n` represents card id `n`, with ranks `23456789TJQKA` and suits `cdhs` (`id = rankIndex * 4 + suitIndex`).

Current-street export request:

```json
{"history":[0,0,0],"max_nodes":100000}
```

The bridge result contains `payload` and `node_count`. Native payload nodes use `type` values `action`, `chance`, and `terminal`. Action `childrens` are aligned with `valid_actions`; current-street chance nodes have empty `childrens` and form the boundary to the next fragment.

Action strategy data includes:

- `card_strings`;
- `reach_probs`;
- `strategy_probs`;
- `action_evs`;
- `evs`;
- other native fields such as `node_avg_ev`, when supplied by the solver.

## Full-tree conclusion

There is no exposed monolithic complete-tree save method in the TexasSolverGPU v0.2.0 frontend/native bridge. Complete persistence is implemented by exhaustively exporting every current-street root reachable through the verified history and legal-card APIs. See `FULL_TREE_EXPORT.md` for evidence and archive details.

The following names came only from a discarded experiment and remain forbidden unless a future runtime proves them:

```text
solver.export.fullTree
solver.export.allStreets
solver.export.fullStrategy
solver.export.strategy
solver.export.tree
solver.dump.strategy
solver.dump.result
```

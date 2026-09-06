# Native bridge schema (TexasSolverGPU v0.2.0 `_131`)

## Envelope

Initial request:

```json
{"id":"rpc_1","method":"bridge.ping","params":{}}
```

Authenticated request:

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

Response:

```json
{"id":"rpc_2","ok":true,"result":{}}
```

or:

```json
{"id":"rpc_2","ok":false,"error":{"code":"...","message":"..."}}
```

For bodyless GET requests the `body` property must be omitted, not set to
`null`. This distinction is required by the v0.2.0 native handler.

## Methods used by the runner

| Native method | Compatibility path | HTTP verb | `body` |
| --- | --- | --- | --- |
| `solver.init` | `/api/init` | POST | native tree configuration below |
| `solver.allocate` | `/api/allocate` | POST | `{"enable_compression":false}` |
| `solver.solve.start` | `/api/gpu-solve` | POST | `{"max_iterations":1000,"target_exploitability":0.5,"compute_initial_exploitability":true,"verbose":false}` |
| `solver.solve.status` | `/api/solve/status` | GET | omitted |
| `solver.solve.stop` | `/api/solve/stop` | POST | `{}` |
| `solver.history.apply` | `/api/apply-history` | POST | `{"history":[0,1]}` |
| `solver.node.actionsAfter` | `/api/actions-after` | POST | `{"append":[]}` |
| `solver.node.currentPlayer` | `/api/current-player` | GET | omitted |
| `solver.node.currentBoard` | `/api/current-board` | GET | omitted |
| `solver.node.numActions` | `/api/num-actions` | GET | omitted |
| `solver.node.results` | `/api/results` | GET | omitted |
| `solver.cards.private` | `/api/private-cards/0` | GET | omitted |
| `solver.export.currentStreet` | `/api/export/current-street` | POST | `{"history":[0,1],"max_nodes":5000}` |

`solver.cards.private` also requires the player id to remain present in `path`.

## `solver.init.body`

```json
{
  "oop_range": [1326 numbers],
  "ip_range": [1326 numbers],
  "board": [19, 51, 24],
  "starting_pot": 55,
  "effective_stack": 975,
  "rake_rate": 0,
  "rake_cap": 0,
  "oop_flop_bet": "",
  "oop_flop_raise": "60%",
  "ip_flop_bet": "33%",
  "ip_flop_raise": "100%",
  "oop_turn_bet": "100%",
  "oop_turn_raise": "100%",
  "ip_turn_bet": "100%",
  "ip_turn_raise": "100%",
  "oop_river_bet": "100%",
  "oop_river_raise": "100%",
  "ip_river_bet": "100%",
  "ip_river_raise": "100%",
  "donk_option": true,
  "oop_turn_donk": "100%",
  "oop_river_donk": "100%",
  "max_raise_number": 3,
  "add_allin_threshold": 2.0,
  "force_allin_threshold": 0.2,
  "add_allin_flop_ip": true,
  "add_allin_turn_ip": true,
  "add_allin_river_ip": true,
  "add_allin_flop_oop": true,
  "add_allin_turn_oop": true,
  "add_allin_river_oop": true,
  "merging_threshold": 0.1,
  "num_players": 2
}
```

Card ids use `rankIndex * 4 + suitIndex`, ranks `23456789TJQKA`, suits `cdhs`.
Thus `6s As 8c` is `[19, 51, 24]`.

Sizing strings are normalized exactly like the shipped frontend: bare numeric
tokens gain `%`; `allin` remains `allin`.

## Structured export result

`solver.export.currentStreet.result` is either the payload itself or:

```json
{"payload": {"type":"action", "strategy": {}}}
```

At an action node the relevant fields are:

- `valid_actions: string[]`
- `strategy.card_strings: string[]`
- `strategy.reach_probs: number[]`
- `strategy.strategy_probs: number[action][]`
- `strategy.action_evs: number[action][]`
- `strategy.evs: number[]` (mixed EV)
- `strategy.node_avg_ev: number`

All per-combo arrays must have the same outer length. Inner strategy/EV arrays
must match `valid_actions.length`.

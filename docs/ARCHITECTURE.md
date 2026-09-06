# Architecture findings

## Boundary found

`TexasSolverGpu_131.exe` is both the WebView2 desktop host and the native GPU
solver. `WebView2Loader.dll` is the only adjacent native DLL. The executable
contains CUDA Driver API calls and embedded frontend assets.

The application page communicates with native code using:

```text
window.chrome.webview.postMessage(JSON.stringify(request))
```

Native responses return through the WebView2 `message` event. Requests and
responses correlate by `id`.

The frontend maps familiar `/api/...` paths to native method names. This map is
an internal compatibility adapter, not proof of a TCP HTTP service. The default
transport selected by the embedded frontend is `bridge`. An HTTP transport is
only a fallback/frontend development path.

## Production integration

The runner launches the unmodified host with a child-process-only WebView2 remote
debugging port. Chrome DevTools Protocol evaluates a small bridge client inside
the application page. That client sends the same WebView2 messages as the
shipped frontend.

This retains:

- the exact `_131.exe` GPU/CUDA engine;
- the native tree builder, allocator, solve loop and exporter;
- the original executable and frontend bytes;
- semantic API calls rather than pixels, coordinates or timing-dependent UI
  clicks.

## Solve sequence

1. `bridge.ping` obtains `bridge_token`.
2. `solver.init` builds the tree from native snake_case configuration.
3. `solver.allocate` allocates the uncompressed GPU tree.
4. `solver.solve.start` starts the asynchronous GPU solve.
5. `solver.solve.status` is polled until `running` becomes false.
6. `solver.history.apply([])` moves to the root.
7. `solver.node.actionsAfter` finds the BB `Check` action by label.
8. `solver.node.actionsAfter` selects the configured UTG bet (a single bet is
   unambiguous; multiple sizes require `-ExpectedBetAmount`).
9. `solver.history.apply(history)` moves to the BB decision.
10. `solver.export.currentStreet` returns the engine's structured node JSON.
11. The runner maps `Fold`, `Call`, and `Raise` by labels and writes compact
    records.

## Evidence from the supplied artifacts

- The public source archive identifies itself as a distribution repository and
  excludes the private `gpu_solver` source tree.
- `TexasSolverGpu_131.exe` imports WebView2 and Winsock and contains embedded
  frontend/native method strings.
- The frontend source embedded in the executable defaults to bridge transport.
- The supplied reference node is board `6sAs8c`, pot `73`, player `0`, with
  actions `Fold`, `Call`, `Raise 73` and 373 combos.

## Risks and limitations

- WebView2 remote debugging must not be disabled by machine policy.
- The DevTools port is bound to loopback and exists only while the child solver
  is running. The runner chooses a free ephemeral port.
- A host update can change bridge method names, auth rules or frontend origin.
  The runner records the solver executable SHA-256 in every `run.json`.
- A solve is iterative. Exact floating-point arrays can vary when convergence
  stops on a nearby iteration; structural and tolerance-based comparison is
  required.
- All five Stage E boards completed successfully on the target machine. The
  reference board matched the GUI export with zero deltas in strategy, action
  EV, mixed EV and reach probability.
- The production runner supports an arbitrary number of flop lines and isolates
  failures by starting one native host per board. It has no Parquet writer or
  disk-space quota.
- Window suppression is implemented outside the solver with an exact-path
  WinEvent hook plus continuous top-level-window enumeration. No solver or
  frontend bytes are patched.

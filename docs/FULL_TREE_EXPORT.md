# Full solved-tree persistence

## Proven mechanism

TexasSolverGPU v0.2.0 does not expose a monolithic full-tree bridge method. The installed frontend maps only `POST /api/export/current-street` to `solver.export.currentStreet`, and the GUI labels the operation “Export Current Street JSON”. The installed native binary contains the same method/path and current-street serializer fields, but no full-tree/dump bridge method.

The public `bupticybee/TexasSolverGPU` repository is a distribution repository; the GPU solver implementation is private. The older open-source CPU TexasSolver has a recursive `dump_result`/`dumps` implementation, but that command and symbol are not exposed by the GPU v0.2.0 desktop runtime. It is therefore not used or inferred here.

The complete postflop solution is persisted after one solve by composing three verified stock operations:

1. `solver.export.currentStreet` exports the native recursive action subtree for one street and stops at chance boundaries.
2. `solver.history.apply` selects each exact chance/action history in the already-solved in-memory tree.
3. `solver.cards.possible` returns the legal-card bit mask at that chance node.

The exporter writes the flop fragment, every legal turn fragment below every flop chance boundary, and every legal river fragment below every turn chance boundary. It never calls `solver.init`, `solver.allocate` or `solver.solve.start` again during persistence.

No guessed method names are probed.

## GPU proof

The diagnostic `scripts/diagnose-full-tree.ps1` was run on the Windows/NVIDIA host with board `6s As 8c`. One solve was followed by native exports for:

- flop root, betting round 1;
- turn `2c`, betting round 2;
- river `2d`, betting round 3.

Every exported action node contained `card_strings`, `reach_probs`, `strategy_probs`, `action_evs`, and `evs`. The proof files were produced under `_diagnostics/`, which is intentionally ignored by Git.

## Archive format

Each board output contains `full-tree.tsgpu.zip`. The archive uses ZIP64-compatible Deflate compression and contains:

- `manifest.json` — format/version, completion flag, solver/config/runner identity, solve parameters and totals;
- `index.jsonl` — one record per native street fragment, keyed by the exact integer history;
- `fragments/flop/*.json` — native flop current-street payloads;
- `fragments/turn/*.json` — native turn current-street payloads;
- `fragments/river/*.json` — native river current-street payloads;
- `metadata/config.json` — exact input config;
- `metadata/tsgpu-worker.ps1` and `metadata/FullTree-Export.ps1` — exact persistence source used for the run.

Each index record stores the fragment SHA256, raw byte count, native node count, validated node counts, chance-boundary histories, legal cards and child histories. Chance edges are references to another indexed fragment rather than duplicated embedded JSON. This preserves all native payload fields while keeping the archive compact and randomly addressable.

The sibling `full-tree.manifest.json` and `run.json` include the final archive SHA256 and byte size. `full-tree.tsgpu.zip` is created only when every discovered chance edge has a corresponding fragment. Interrupted or deliberately limited development runs retain a differently named incomplete archive and can never be mistaken for a complete result.

## Offline validation and extraction

The validator uses only the Python standard library and does not contact or start the solver:

```powershell
python .\scripts\inspect-full-tree.py .\output\smoke\0001_6s_As_8c\full-tree.tsgpu.zip --deep
```

`--deep` decompresses every fragment, verifies its SHA256 and byte count, parses every native node, checks the betting round and required strategy fields, and proves that every indexed chance edge resolves to the next street.

To extract a later street fragment or a decision below it:

```powershell
python .\scripts\inspect-full-tree.py TREE.zip --history "0,0,0" --path "0,1" --output node.json
```

Histories are the exact integer histories accepted by `solver.history.apply`; `--path` is an action-index path inside that street fragment.

## Operational limits

- A full tree contains tens of thousands of native fragments and is much larger/slower to export than one selected node.
- The solver process must remain alive until export completes. A host/GPU failure cannot be resumed without solving again because TexasSolverGPU v0.2.0 exposes no solved-state reload API.
- The archive is tied to the installed TexasSolverGPU v0.2.0 schema. Consumers must check `schema_version`, hashes and `complete`.
- The archive intentionally retains native JSON; report-specific CSV/Parquet is generated later from it without another solve.

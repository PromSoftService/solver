# Five-flop example

Run from the repository root:

```powershell
.\tsgpu-batch.cmd .\example\config.json .\example\boards.txt .\output\example-five-flops
```

The example solves UTG 2.5bb open versus BB call with pot 55 and effective stack 975 (money scale x10). OOP flop betting is disabled; IP has one 33% flop bet and OOP raises 60%, producing expected amounts 18 and 73.

`runner.decisionNode` selects the exported branch. Here `BB_RESPONSE` means BB check -> UTG bet 33% -> BB decision. The two expected amounts guard against silently selecting the wrong action tree.

Each board gets its own numbered output directory containing `run.json`, `node.raw.json`, `combos.json`, `combos.csv`, and `bridge-transcript.jsonl`. The batch root contains `batch-summary.json` and `batch-summary.csv`.

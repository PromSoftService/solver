#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8-sig')


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def replace_once(rel, old, new):
    text = read(rel)
    if text.count(old) != 1:
        raise RuntimeError(f'{rel}: expected one occurrence of {old!r}, found {text.count(old)}')
    write(rel, text.replace(old, new, 1))


old_validate = "[ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET', 'BTN_RESPONSE', 'BTN_STAB')][string]$DecisionNode = 'BB_RESPONSE'"
new_validate = "[ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET', 'BTN_RESPONSE', 'BTN_STAB', 'UTG_RESPONSE')][string]$DecisionNode = 'BB_RESPONSE'"
for rel in ('tsgpu-worker.ps1', 'tsgpu-batch.ps1', 'scripts/Run-Study.ps1'):
    replace_once(rel, old_validate, new_validate)

# Worker: select UTG response after UTG check -> BTN B33.
worker = read('tsgpu-worker.ps1')
worker = worker.replace("$ScriptVersion = 'v014-production'", "$ScriptVersion = 'v015-production'", 1)
old = """        } elseif ($DecisionNode -eq 'BTN_STAB') {
            # Export BTN's Check/Bet decision after UTG checks the flop root.
            $exportHistory = @($history)
            $selectedActions = @($check.Label)
            $actingPlayer = 'BTN'
        } else {
            $bet = Find-ActionIndex $ipActions 'Bet' ([Nullable[int]]$ExpectedBetAmount)
            $history = @($history + [int]$bet.Index)
            Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $transcript | Out-Null
            $exportHistory = @($history)
            $selectedActions = @($check.Label, $bet.Label)
            $actingPlayer = 'BB'
        }
"""
new = """        } elseif ($DecisionNode -eq 'BTN_STAB') {
            # Export BTN's Check/Bet decision after UTG checks the flop root.
            $exportHistory = @($history)
            $selectedActions = @($check.Label)
            $actingPlayer = 'BTN'
        } elseif ($DecisionNode -eq 'UTG_RESPONSE') {
            # Export UTG's Fold/Call/Raise response after UTG checks and BTN bets 33%.
            # Native APIs may label the first IP wager Bet or Raise, so accept either.
            $bet = $null
            try {
                $bet = Find-ActionIndex $ipActions 'Bet' ([Nullable[int]]$ExpectedBetAmount)
            } catch {
                $bet = Find-ActionIndex $ipActions 'Raise' ([Nullable[int]]$ExpectedBetAmount)
            }
            $history = @($history + [int]$bet.Index)
            Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $transcript | Out-Null
            $exportHistory = @($history)
            $selectedActions = @($check.Label, $bet.Label)
            $actingPlayer = 'UTG'
        } else {
            $bet = Find-ActionIndex $ipActions 'Bet' ([Nullable[int]]$ExpectedBetAmount)
            $history = @($history + [int]$bet.Index)
            Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $transcript | Out-Null
            $exportHistory = @($history)
            $selectedActions = @($check.Label, $bet.Label)
            $actingPlayer = 'BB'
        }
"""
if worker.count(old) != 1:
    raise RuntimeError('worker BTN_STAB/default selection block changed unexpectedly')
worker = worker.replace(old, new, 1)
write('tsgpu-worker.ps1', worker)

# Collector: infer UTG and emit *_utg F/C/R fields for NOD006.
collector = read('tools/collect_dataset.ps1')
collector = collector.replace(
    "} elseif ($decisionNode -in @('UTG_CBET', 'UTG_OOP_CBET')) {\n        'UTG'",
    "} elseif ($decisionNode -in @('UTG_CBET', 'UTG_OOP_CBET', 'UTG_RESPONSE')) {\n        'UTG'",
    1,
)
collector = collector.replace(
    "$suffix = if ($actingPlayer -eq 'BTN') { 'btn' } else { 'bb' }",
    "$suffix = if ($actingPlayer -eq 'BTN') { 'btn' } elseif ($actingPlayer -eq 'UTG') { 'utg' } else { 'bb' }",
    1,
)
write('tools/collect_dataset.ps1', collector)

# CFG003 metadata: OOP raise60 after BTN B33 => native Raise 85.
spec_rel = 'configs/CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.derived.json'
spec = json.loads(read(spec_rel))
spec.setdefault('expected_native_actions', {})['utg_response_raise'] = 85
write(spec_rel, json.dumps(spec, ensure_ascii=False, indent=2) + '\n')

# NOD006 launcher from the proven NOD005 materialization path.
base = read('scripts/Run-CFG003-NOD005-BRD001.ps1')
n6 = base.replace('NOD005', 'NOD006')
n6 = n6.replace("DecisionNode = 'BTN_STAB'", "DecisionNode = 'UTG_RESPONSE'")
n6 = n6.replace(
    'Write-Host "NOD006: export BTN stab decision after UTG check; expected native Bet $($spec.expected_native_actions.btn_stab_bet)"',
    'Write-Host "NOD006: export UTG response after UTG check -> BTN B33; expected native Bet $($spec.expected_native_actions.btn_stab_bet), Raise $($spec.expected_native_actions.utg_response_raise)"'
)
n6 = n6.replace('ExpectedRaiseAmount = 0', 'ExpectedRaiseAmount = [int]$spec.expected_native_actions.utg_response_raise')
write('scripts/Run-CFG003-NOD006-BRD001.ps1', n6)

cmd = read('scripts/RUN__CFG003__NOD005__BRD001.cmd').replace('NOD005', 'NOD006')
write('scripts/RUN__CFG003__NOD006__BRD001.cmd', cmd)

and_push = r'''@echo off
setlocal EnableExtensions

call "%~dp0RUN__CFG003__NOD006__BRD001.cmd"
if errorlevel 1 (
  echo NOD006 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD006__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

pushd "%~dp0.."
git add -- "datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-*.csv" "datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-*.manifest.json"
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "add RNG002 CFG003 NOD006 BRD001 dataset"
  if errorlevel 1 (
    popd
    exit /b %ERRORLEVEL%
  )
  git push
  if errorlevel 1 (
    popd
    exit /b %ERRORLEVEL%
  )
) else (
  echo No new NOD006 dataset files to commit.
)
popd
exit /b 0
'''
write('scripts/RUN__CFG003__NOD006__BRD001__AND_PUSH.cmd', and_push)

# Registry/docs.
registry = read('docs/STUDY_REGISTRY.md')
needle = "| `NOD005` | `BTN_STAB` | BTN | after `UTG Check` at the CFG003 flop root; `Check / Bet 33%` |"
if needle not in registry:
    raise RuntimeError('registry NOD005 row not found')
registry = registry.replace(needle, needle + "\n| `NOD006` | `UTG_RESPONSE` | UTG | after `UTG Check -> BTN Bet 33%`; `Fold / Call / Raise 60%` |", 1)
needle2 = "`NOD005` exports BTN's stab decision after `UTG Check`. BTN actions are `Check / Bet 33%`; the expected native wager is 21. The dataset uses BTN-specific `ev_check_btn`, `ev_bet_btn`, `mixed_ev_btn`, and `loss_if_*_btn` fields."
registry = registry.replace(needle2, needle2 + "\n\n`NOD006` exports UTG's response after `UTG Check -> BTN Bet 33%`. UTG actions are `Fold / Call / Raise 60%`; expected native amounts are BTN Bet 21 and UTG Raise 85. The dataset uses UTG-specific `ev_fold_utg`, `ev_call_utg`, `ev_raise_utg`, `mixed_ev_utg`, and `loss_if_*_utg` fields.", 1)
registry = registry.replace(".\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n", ".\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD006__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD006__BRD001__AND_PUSH.cmd\n", 1)
write('docs/STUDY_REGISTRY.md', registry)

readme = read('README.md')
readme = readme.replace("- `NOD005 / BTN_STAB`: export BTN Check/Bet 33% after UTG checks the CFG003 flop root.", "- `NOD005 / BTN_STAB`: export BTN Check/Bet 33% after UTG checks the CFG003 flop root.\n- `NOD006 / UTG_RESPONSE`: export UTG Fold/Call/Raise 60% after UTG checks and BTN bets 33%.", 1)
readme = readme.replace(".\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n", ".\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD006__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD006__BRD001__AND_PUSH.cmd\n", 1)
readme += "\n### UTG defense versus BTN stab on CFG003\n\n`NOD006` studies `UTG Check -> BTN Bet 33% -> UTG Fold/Call/Raise 60%`. It reuses `RNG002`, `CFG003`, and `BRD001`. Expected native amounts are BTN Bet 21 and UTG Raise 85. The `AND_PUSH` launcher retries one incomplete run once, then commits and pushes only the generated NOD006 dataset and manifest.\n"
write('README.md', readme)

agents = read('AGENTS.md')
if 'NOD006 / UTG_RESPONSE' not in agents:
    agents += "\n- `NOD006 / UTG_RESPONSE`: UTG Fold/Call/Raise after `UTG Check -> BTN Bet 33%`; expected native BTN wager 21 and UTG Raise 85; F/C/R dataset fields use the `*_utg` suffix.\n"
write('AGENTS.md', agents)

# Focused CI for the new node.
workflow = r'''name: Runner v015 UTG response checks

on:
  push:
    branches: [main]
    paths:
      - 'tsgpu-worker.ps1'
      - 'tsgpu-batch.ps1'
      - 'scripts/Run-Study.ps1'
      - 'scripts/Run-CFG003-NOD006-BRD001.ps1'
      - 'scripts/RUN__CFG003__NOD006__BRD001.cmd'
      - 'scripts/RUN__CFG003__NOD006__BRD001__AND_PUSH.cmd'
      - 'configs/CFG003__*.derived.json'
      - 'tools/collect_dataset.ps1'
      - '.github/workflows/runner-v015-utg-response-check.yml'
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Parse PowerShell scripts
        shell: pwsh
        run: |
          $failed = $false
          foreach ($path in @(
            'tsgpu-worker.ps1',
            'tsgpu-batch.ps1',
            'scripts/Run-Study.ps1',
            'scripts/Run-CFG003-NOD006-BRD001.ps1',
            'tools/collect_dataset.ps1'
          )) {
            $tokens = $null
            $errors = $null
            [void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $path), [ref]$tokens, [ref]$errors)
            if ($errors.Count -gt 0) {
              Write-Host "Parser errors in $path"
              $errors | ForEach-Object { Write-Host $_.Message }
              $failed = $true
            }
          }
          if ($failed) { exit 1 }

      - name: Test NOD006 wiring
        shell: pwsh
        run: |
          foreach ($path in @('tsgpu-worker.ps1','tsgpu-batch.ps1','scripts/Run-Study.ps1','scripts/Run-CFG003-NOD006-BRD001.ps1')) {
            $text = Get-Content -LiteralPath $path -Raw
            if ($text -notmatch 'UTG_RESPONSE') { throw "UTG_RESPONSE missing from $path" }
          }
          $worker = Get-Content -LiteralPath ./tsgpu-worker.ps1 -Raw
          if ($worker -notmatch "DecisionNode -eq 'UTG_RESPONSE'") { throw 'Worker does not select UTG response node.' }
          if ($worker -notmatch "actingPlayer = 'UTG'") { throw 'UTG acting-player assignment missing.' }
          $spec = Get-Content -LiteralPath './configs/CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.derived.json' -Raw | ConvertFrom-Json
          if ([int]$spec.expected_native_actions.btn_stab_bet -ne 21) { throw 'Unexpected BTN stab bet.' }
          if ([int]$spec.expected_native_actions.utg_response_raise -ne 85) { throw 'Unexpected UTG response raise.' }

      - name: Test UTG response dataset schema
        shell: pwsh
        run: |
          $root = Join-Path $PWD '_collector_utg_response_test'
          $job = Join-Path $root '0001_As_Kh_Qd'
          New-Item -ItemType Directory -Path $job -Force | Out-Null
          '{"schema_version":2,"decision_node":"UTG_RESPONSE","acting_player":"UTG","board":"As Kh Qd","final_status":{"iteration":1000,"exploitability":0.5}}' | Set-Content -LiteralPath (Join-Path $job 'run.json') -Encoding UTF8
          '[{"combo":"AcKd","reach_probability":0.5,"fold_frequency":0.2,"call_frequency":0.6,"raise_frequency":0.2,"ev_fold":5.0,"ev_call":9.0,"ev_raise":10.0,"mixed_ev":8.8}]' | Set-Content -LiteralPath (Join-Path $job 'combos.json') -Encoding UTF8
          & ./tools/collect_dataset.ps1 -OutputDir $root -MoneyScale 10
          $r = Import-Csv (Join-Path $root 'dataset.csv') | Select-Object -First 1
          if ([math]::Abs([double]$r.ev_raise_utg - 1.0) -gt 0.000001) { throw 'UTG response EV scaling failed.' }
          if ([math]::Abs([double]$r.loss_if_fold_utg - 0.5) -gt 0.000001) { throw 'UTG response loss field failed.' }
          if ($null -ne $r.PSObject.Properties['ev_raise_bb']) { throw 'UTG response leaked BB suffix.' }

      - name: Check launchers and docs
        shell: bash
        run: |
          test -f scripts/RUN__CFG003__NOD006__BRD001.cmd
          test -f scripts/RUN__CFG003__NOD006__BRD001__AND_PUSH.cmd
          grep -q 'NOD006' docs/STUDY_REGISTRY.md
          grep -q 'UTG_RESPONSE' README.md
          git diff --check
'''
write('.github/workflows/runner-v015-utg-response-check.yml', workflow)

print('NOD006 patch applied')

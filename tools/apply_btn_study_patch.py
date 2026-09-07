#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8-sig')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_exact(rel, old, new, count=None):
    text = read(rel)
    found = text.count(old)
    expected = 1 if count is None else count
    if found != expected:
        raise RuntimeError(f'{rel}: expected {expected} occurrences, found {found}: {old!r}')
    write(rel, text.replace(old, new))


# ---------------------------------------------------------------------------
# Worker: add two immutable BTN decision-node modes on the existing CFG003 tree.
# ---------------------------------------------------------------------------
worker_rel = 'tsgpu-worker.ps1'
worker = read(worker_rel)
old_validate = "[ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET')][string]$DecisionNode = 'BB_RESPONSE'"
new_validate = "[ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET', 'BTN_RESPONSE', 'BTN_STAB')][string]$DecisionNode = 'BB_RESPONSE'"
if worker.count(old_validate) != 1:
    raise RuntimeError('worker ValidateSet changed unexpectedly')
worker = worker.replace(old_validate, new_validate)
worker = worker.replace("$ScriptVersion = 'v013-production'", "$ScriptVersion = 'v014-production'", 1)

selection_pattern = re.compile(
    r"    if \(\$DecisionNode -eq 'UTG_OOP_CBET'\) \{.*?\n    \$export = Invoke-Bridge",
    re.S,
)
selection_match = selection_pattern.search(worker)
if not selection_match:
    raise RuntimeError('worker decision-selection block not found')
new_selection = r'''    if ($DecisionNode -eq 'UTG_OOP_CBET') {
        # Export the flop root before UTG acts. This is the OOP UTG decision in
        # UTG-open / BTN-call single-raised pots.
        $exportHistory = @()
        $selectedActions = @()
        $actingPlayer = 'UTG'
    } elseif ($DecisionNode -eq 'BTN_RESPONSE') {
        # Export BTN's Fold/Call/Raise response after UTG bets at the flop root.
        # Native APIs may label a first wager Bet or Raise, so accept either.
        $rootBet = $null
        try {
            $rootBet = Find-ActionIndex $rootActions 'Bet' ([Nullable[int]]$ExpectedBetAmount)
        } catch {
            $rootBet = Find-ActionIndex $rootActions 'Raise' ([Nullable[int]]$ExpectedBetAmount)
        }
        $history = @([int]$rootBet.Index)
        Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $transcript | Out-Null
        $exportHistory = @($history)
        $selectedActions = @($rootBet.Label)
        $actingPlayer = 'BTN'
    } else {
        $check = Find-ActionIndex $rootActions 'Check' $null
        $history = @([int]$check.Index)

        Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $transcript | Out-Null
        $ipActions = Split-Actions (Invoke-Bridge $socket 'solver.node.actionsAfter' '/api/actions-after' 'POST' ([ordered]@{ append = @() }) 10000 $transcript)

        if ($DecisionNode -eq 'UTG_CBET') {
            # We export the node immediately after BB checks, so no UTG action is
            # applied here. Native APIs are inconsistent about naming the first IP
            # wager after a check (Bet vs Raise), therefore do not preselect it.
            $exportHistory = @($history)
            $selectedActions = @($check.Label)
            $actingPlayer = 'UTG'
        } elseif ($DecisionNode -eq 'BTN_STAB') {
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
    }

    $export = Invoke-Bridge'''
worker = worker[:selection_match.start()] + new_selection + worker[selection_match.end():]

old_check_nodes = "@('UTG_CBET', 'UTG_OOP_CBET')"
if worker.count(old_check_nodes) != 2:
    raise RuntimeError(f'worker expected two UTG check/bet node lists, found {worker.count(old_check_nodes)}')
worker = worker.replace(old_check_nodes, "@('UTG_CBET', 'UTG_OOP_CBET', 'BTN_STAB')")
worker = worker.replace('Required UTG wager action is missing:', 'Required wager action is missing:')
worker = worker.replace('Expected UTG wager $ExpectedBetAmount, got:', 'Expected wager $ExpectedBetAmount, got:')
write(worker_rel, worker)

# Batch / study orchestration: accept the new modes.
for rel in ('tsgpu-batch.ps1', 'scripts/Run-Study.ps1'):
    text = read(rel)
    if text.count(old_validate) != 1:
        raise RuntimeError(f'{rel}: ValidateSet changed unexpectedly')
    write(rel, text.replace(old_validate, new_validate))

# ---------------------------------------------------------------------------
# Collector: preserve old schemas while adding explicit BTN-named schemas.
# ---------------------------------------------------------------------------
collector = r'''param(
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [double]$MoneyScale = 10.0
)
$ErrorActionPreference = 'Stop'
$rows = New-Object System.Collections.Generic.List[object]
$datasetDecisionNode = $null

Get-ChildItem -LiteralPath $OutputDir -Directory | Sort-Object Name | ForEach-Object {
    $runPath = Join-Path $_.FullName 'run.json'
    $comboPath = Join-Path $_.FullName 'combos.json'
    if (-not (Test-Path -LiteralPath $runPath) -or -not (Test-Path -LiteralPath $comboPath)) { return }
    $run = Get-Content -LiteralPath $runPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $combos = Get-Content -LiteralPath $comboPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $decisionProperty = $run.PSObject.Properties['decision_node']
    $decisionNode = if ($null -ne $decisionProperty -and $decisionProperty.Value) { [string]$decisionProperty.Value } else { 'BB_RESPONSE' }
    $actingProperty = $run.PSObject.Properties['acting_player']
    $actingPlayer = if ($null -ne $actingProperty -and $actingProperty.Value) {
        ([string]$actingProperty.Value).ToUpperInvariant()
    } elseif ($decisionNode -in @('BTN_RESPONSE', 'BTN_STAB')) {
        'BTN'
    } elseif ($decisionNode -in @('UTG_CBET', 'UTG_OOP_CBET')) {
        'UTG'
    } else {
        'BB'
    }
    if ($null -eq $datasetDecisionNode) { $datasetDecisionNode = $decisionNode }
    if ($datasetDecisionNode -ne $decisionNode) { throw "Mixed decision nodes in one output directory: $datasetDecisionNode and $decisionNode." }

    foreach ($x in $combos) {
        if ($decisionNode -in @('UTG_CBET', 'UTG_OOP_CBET', 'BTN_STAB')) {
            $check = [double]$x.check_frequency
            $bet = [double]$x.bet_frequency
            $evCheck = [double]$x.ev_check / $MoneyScale
            $evBet = [double]$x.ev_bet / $MoneyScale
            $mixed = [double]$x.mixed_ev / $MoneyScale
            $best = 'X'; $bestEv = $evCheck
            if ($evBet -gt $bestEv) { $best='B'; $bestEv=$evBet }
            $freqAction='X'; $freq=$check
            if ($bet -gt $freq) { $freqAction='B'; $freq=$bet }
            $suffix = if ($actingPlayer -eq 'BTN') { 'btn' } else { 'utg' }
            $row = [ordered]@{
                board = $run.board
                combo = $x.combo
                reach_probability = [double]$x.reach_probability
                check_frequency = $check
                bet_frequency = $bet
            }
            $row["ev_check_$suffix"] = $evCheck
            $row["ev_bet_$suffix"] = $evBet
            $row["mixed_ev_$suffix"] = $mixed
            $row['best_ev_action'] = $best
            $row["best_ev_$suffix"] = $bestEv
            $row['highest_frequency_action'] = $freqAction
            $row['highest_frequency'] = $freq
            $row["loss_if_check_$suffix"] = $bestEv - $evCheck
            $row["loss_if_bet_$suffix"] = $bestEv - $evBet
            $row['iteration'] = $run.final_status.iteration
            $row['exploitability'] = $run.final_status.exploitability
            $rows.Add([pscustomobject]$row) | Out-Null
        } else {
            $f = [double]$x.fold_frequency
            $c = [double]$x.call_frequency
            $r = [double]$x.raise_frequency
            $evF = [double]$x.ev_fold / $MoneyScale
            $evC = [double]$x.ev_call / $MoneyScale
            $evR = [double]$x.ev_raise / $MoneyScale
            $mixed = [double]$x.mixed_ev / $MoneyScale
            $best = 'F'; $bestEv = $evF
            if ($evC -gt $bestEv) { $best='C'; $bestEv=$evC }
            if ($evR -gt $bestEv) { $best='R'; $bestEv=$evR }
            $freqAction='F'; $freq=$f
            if ($c -gt $freq) { $freqAction='C'; $freq=$c }
            if ($r -gt $freq) { $freqAction='R'; $freq=$r }
            $suffix = if ($actingPlayer -eq 'BTN') { 'btn' } else { 'bb' }
            $row = [ordered]@{
                board = $run.board
                combo = $x.combo
                reach_probability = [double]$x.reach_probability
                fold_frequency = $f
                call_frequency = $c
                raise_frequency = $r
            }
            $row["ev_fold_$suffix"] = $evF
            $row["ev_call_$suffix"] = $evC
            $row["ev_raise_$suffix"] = $evR
            $row["mixed_ev_$suffix"] = $mixed
            $row['best_ev_action'] = $best
            $row["best_ev_$suffix"] = $bestEv
            $row['highest_frequency_action'] = $freqAction
            $row['highest_frequency'] = $freq
            $row["loss_if_fold_$suffix"] = $bestEv - $evF
            $row["loss_if_call_$suffix"] = $bestEv - $evC
            $row["loss_if_raise_$suffix"] = $bestEv - $evR
            $row['iteration'] = $run.final_status.iteration
            $row['exploitability'] = $run.final_status.exploitability
            $rows.Add([pscustomobject]$row) | Out-Null
        }
    }
}
if ($rows.Count -eq 0) { throw 'No */run.json + combos.json pairs found.' }
$out = Join-Path $OutputDir 'dataset.csv'
$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Host "Wrote $($rows.Count) rows ($datasetDecisionNode) -> $out"
'''
write('tools/collect_dataset.ps1', collector)

# Config metadata: same immutable CFG003 tree, additional expected action amounts.
spec_rel = 'configs/CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.derived.json'
spec = json.loads(read(spec_rel))
spec.setdefault('expected_native_actions', {})['utg_root_bet'] = 21
spec['expected_native_actions']['btn_stab_bet'] = 21
spec['expected_native_actions']['btn_response_raise'] = 128
spec['notes'] = ('UTG is OOP versus BTN. Root actions are Check / Bet 33%. If UTG checks, BTN has Check / Bet 33%. '
                 'If UTG bets 33%, BTN has Fold / Call / Raise 100%. Future turn/river sizings, all-in settings and rake settings are inherited from CFG001.')
write(spec_rel, json.dumps(spec, indent=2, ensure_ascii=False) + '\n')

# ---------------------------------------------------------------------------
# Registered launchers. Reuse the existing proven CFG003 materialization logic.
# ---------------------------------------------------------------------------
base = read('scripts/Run-CFG003-NOD003-BRD001.ps1')

nod4 = base.replace('NOD003', 'NOD004')
nod4 = nod4.replace("DecisionNode = 'UTG_OOP_CBET'", "DecisionNode = 'BTN_RESPONSE'")
nod4 = nod4.replace(
    'Write-Host "NOD004: export UTG root decision; expected native Bet $($spec.expected_native_actions.utg_root_bet)"',
    'Write-Host "NOD004: export BTN response after UTG B33; expected native Raise $($spec.expected_native_actions.btn_response_raise)"'
)
nod4 = nod4.replace('ExpectedRaiseAmount = 0', 'ExpectedRaiseAmount = [int]$spec.expected_native_actions.btn_response_raise')
write('scripts/Run-CFG003-NOD004-BRD001.ps1', nod4)

nod5 = base.replace('NOD003', 'NOD005')
nod5 = nod5.replace("DecisionNode = 'UTG_OOP_CBET'", "DecisionNode = 'BTN_STAB'")
nod5 = nod5.replace('expected_native_actions.utg_root_bet', 'expected_native_actions.btn_stab_bet')
nod5 = nod5.replace(
    'Write-Host "NOD005: export UTG root decision; expected native Bet $($spec.expected_native_actions.btn_stab_bet)"',
    'Write-Host "NOD005: export BTN stab decision after UTG check; expected native Bet $($spec.expected_native_actions.btn_stab_bet)"'
)
write('scripts/Run-CFG003-NOD005-BRD001.ps1', nod5)

base_cmd = read('scripts/RUN__CFG003__NOD003__BRD001.cmd')
write('scripts/RUN__CFG003__NOD004__BRD001.cmd', base_cmd.replace('NOD003', 'NOD004'))
write('scripts/RUN__CFG003__NOD005__BRD001.cmd', base_cmd.replace('NOD003', 'NOD005'))

combined_cmd = r'''@echo off
setlocal EnableExtensions

call "%~dp0RUN__CFG003__NOD004__BRD001.cmd"
if errorlevel 1 (
  echo NOD004 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD004__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

call "%~dp0RUN__CFG003__NOD005__BRD001.cmd"
if errorlevel 1 (
  echo NOD005 first pass failed. Retrying incomplete boards once...
  call "%~dp0RUN__CFG003__NOD005__BRD001.cmd" resume
  if errorlevel 1 exit /b %ERRORLEVEL%
)

pushd "%~dp0.."
git add .
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "add RNG002 CFG003 NOD004 NOD005 BRD001 datasets"
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
  echo No new files to commit.
)
popd

echo.
echo BOTH STUDIES COMPLETE AND PUSHED.
exit /b 0
'''
write('scripts/RUN__CFG003__NOD004_NOD005__BRD001__AND_PUSH.cmd', combined_cmd)

# ---------------------------------------------------------------------------
# Docs.
# ---------------------------------------------------------------------------
registry_rel = 'docs/STUDY_REGISTRY.md'
registry = read(registry_rel)
old_table_row = "| `NOD003` | `UTG_OOP_CBET` | UTG | flop root in UTG-vs-BTN SRP, before any flop action; `Check / configured OOP Bet` |"
new_table_rows = old_table_row + "\n| `NOD004` | `BTN_RESPONSE` | BTN | after `UTG Bet 33%` at the CFG003 flop root; `Fold / Call / Raise 100%` |\n| `NOD005` | `BTN_STAB` | BTN | after `UTG Check` at the CFG003 flop root; `Check / Bet 33%` |"
if registry.count(old_table_row) != 1:
    raise RuntimeError('registry NOD003 row changed unexpectedly')
registry = registry.replace(old_table_row, new_table_rows)
anchor = "`NOD003` exports UTG's OOP decision at the **flop root** for `CFG003`, before UTG takes any action. The semantic actions are `Check / Bet 33%`; the launcher validates the native wager amount 21. The exported dataset uses the same UTG check/bet field schema as `NOD002`."
addition = anchor + "\n\n`NOD004` exports BTN's response after `UTG Bet 33%` at the CFG003 root. BTN actions are `Fold / Call / Raise 100%`; native amounts are UTG Bet 21 and BTN Raise 128. The dataset uses BTN-specific `*_btn` EV/loss fields.\n\n`NOD005` exports BTN's stab decision after `UTG Check`. BTN actions are `Check / Bet 33%`; the expected native wager is 21. The dataset uses BTN-specific `ev_check_btn`, `ev_bet_btn`, `mixed_ev_btn`, and `loss_if_*_btn` fields."
if registry.count(anchor) != 1:
    raise RuntimeError('registry NOD003 paragraph changed unexpectedly')
registry = registry.replace(anchor, addition)
launcher_anchor = ".\\scripts\\RUN__CFG003__NOD003__BRD001.cmd\n"
if registry.count(launcher_anchor) != 1:
    raise RuntimeError('registry launcher anchor changed unexpectedly')
registry = registry.replace(launcher_anchor, launcher_anchor + ".\\scripts\\RUN__CFG003__NOD004__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD004_NOD005__BRD001__AND_PUSH.cmd\n")
write(registry_rel, registry)

readme_rel = 'README.md'
readme = read(readme_rel)
old_dec = "- `NOD003 / UTG_OOP_CBET`: export the UTG OOP Check/Bet decision at the flop root before any flop action."
new_dec = old_dec + "\n- `NOD004 / BTN_RESPONSE`: export BTN Fold/Call/Raise after UTG bets 33% at the CFG003 flop root.\n- `NOD005 / BTN_STAB`: export BTN Check/Bet 33% after UTG checks the CFG003 flop root."
if readme.count(old_dec) != 1:
    raise RuntimeError('README NOD003 bullet changed unexpectedly')
readme = readme.replace(old_dec, new_dec)
readme_launcher = ".\\scripts\\RUN__CFG003__NOD003__BRD001.cmd\n"
if readme.count(readme_launcher) != 1:
    raise RuntimeError('README launcher anchor changed unexpectedly')
readme = readme.replace(readme_launcher, readme_launcher + ".\\scripts\\RUN__CFG003__NOD004__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD005__BRD001.cmd\n.\\scripts\\RUN__CFG003__NOD004_NOD005__BRD001__AND_PUSH.cmd\n")
readme += "\n### BTN follow-up studies on CFG003\n\n`NOD004` studies BTN defense versus UTG B33. `NOD005` studies BTN stab after UTG checks. The combined `AND_PUSH` launcher runs NOD004, then NOD005, retries an incomplete run once if necessary, stages generated datasets/manifests with `git add .`, commits them only after both studies complete, and pushes the commit.\n"
write(readme_rel, readme)

# AGENTS handoff: append the newer registered nodes without rewriting old history.
agents_rel = 'AGENTS.md'
agents = read(agents_rel)
marker = "### `NOD002 / UTG_CBET`"
if marker not in agents:
    raise RuntimeError('AGENTS NOD002 marker not found')
append_note = r'''

### Additional registered UTG-vs-BTN nodes

The authoritative current registry is `docs/STUDY_REGISTRY.md`. For `RNG002 / CFG003 / BRD001`:

- `NOD003 / UTG_OOP_CBET`: UTG root Check/Bet 33%;
- `NOD004 / BTN_RESPONSE`: BTN Fold/Call/Raise after UTG root Bet 33%; expected native UTG wager 21 and BTN Raise 128;
- `NOD005 / BTN_STAB`: BTN Check/Bet 33% after UTG root Check; expected native BTN wager 21.

BTN datasets use `*_btn` EV/loss field suffixes. Do not relabel these nodes as UTG or BB decisions.
'''
if '### Additional registered UTG-vs-BTN nodes' not in agents:
    agents += append_note
write(agents_rel, agents)

# ---------------------------------------------------------------------------
# CI: parse the new scripts, verify node wiring, and validate BTN schemas.
# ---------------------------------------------------------------------------
ci_rel = '.github/workflows/runner-v013-check.yml'
ci = read(ci_rel)
ci = ci.replace('name: Runner v013 checks', 'name: Runner v014 checks', 1)
path_anchor = "      - 'scripts/RUN__CFG003__NOD003__BRD001.cmd'\n"
if path_anchor not in ci:
    raise RuntimeError('CI path anchor not found')
ci = ci.replace(path_anchor, path_anchor + "      - 'scripts/Run-CFG003-NOD004-BRD001.ps1'\n      - 'scripts/Run-CFG003-NOD005-BRD001.ps1'\n      - 'scripts/RUN__CFG003__NOD004__BRD001.cmd'\n      - 'scripts/RUN__CFG003__NOD005__BRD001.cmd'\n      - 'scripts/RUN__CFG003__NOD004_NOD005__BRD001__AND_PUSH.cmd'\n")
parse_anchor = "            'scripts/Run-CFG003-NOD003-BRD001.ps1',\n"
if parse_anchor not in ci:
    raise RuntimeError('CI parser anchor not found')
ci = ci.replace(parse_anchor, parse_anchor + "            'scripts/Run-CFG003-NOD004-BRD001.ps1',\n            'scripts/Run-CFG003-NOD005-BRD001.ps1',\n")
wire_anchor = "          if ($worker -notmatch '\\\(\\\?:Bet\\\|Raise\\\)') {\n            throw 'UTG check/bet nodes must accept native Bet/Raise wager aliases.'\n          }\n"
if wire_anchor not in ci:
    raise RuntimeError('CI wiring anchor not found')
ci = ci.replace(wire_anchor, wire_anchor + "          foreach ($node in @('BTN_RESPONSE','BTN_STAB')) {\n            foreach ($text in @($worker,$batch,$study)) {\n              if ($text -notmatch $node) { throw \"$node is missing from runner wiring.\" }\n            }\n          }\n          if ($worker -notmatch \"DecisionNode -eq 'BTN_RESPONSE'\") { throw 'Worker does not select the BTN response node.' }\n          if ($worker -notmatch \"DecisionNode -eq 'BTN_STAB'\") { throw 'Worker does not select the BTN stab node.' }\n")

btn_test = r'''

      - name: Test BTN dataset collector schemas
        shell: pwsh
        run: |
          $root = Join-Path $PWD '_collector_btn_test'
          $stab = Join-Path $root 'stab'
          $stabJob = Join-Path $stab '0001_As_Kh_Qd'
          New-Item -ItemType Directory -Path $stabJob -Force | Out-Null
          '{"schema_version":2,"decision_node":"BTN_STAB","acting_player":"BTN","board":"As Kh Qd","final_status":{"iteration":1000,"exploitability":0.5}}' | Set-Content -LiteralPath (Join-Path $stabJob 'run.json') -Encoding UTF8
          '[{"combo":"AcKd","reach_probability":0.5,"check_frequency":0.25,"bet_frequency":0.75,"ev_check":10.0,"ev_bet":12.0,"mixed_ev":11.5}]' | Set-Content -LiteralPath (Join-Path $stabJob 'combos.json') -Encoding UTF8
          & ./tools/collect_dataset.ps1 -OutputDir $stab -MoneyScale 10
          $s = Import-Csv (Join-Path $stab 'dataset.csv') | Select-Object -First 1
          if ([math]::Abs([double]$s.ev_bet_btn - 1.2) -gt 0.000001) { throw 'BTN stab EV scaling failed.' }
          if ([math]::Abs([double]$s.loss_if_check_btn - 0.2) -gt 0.000001) { throw 'BTN stab loss field failed.' }

          $resp = Join-Path $root 'response'
          $respJob = Join-Path $resp '0001_As_Kh_Qd'
          New-Item -ItemType Directory -Path $respJob -Force | Out-Null
          '{"schema_version":2,"decision_node":"BTN_RESPONSE","acting_player":"BTN","board":"As Kh Qd","final_status":{"iteration":1000,"exploitability":0.5}}' | Set-Content -LiteralPath (Join-Path $respJob 'run.json') -Encoding UTF8
          '[{"combo":"AcKd","reach_probability":0.5,"fold_frequency":0.1,"call_frequency":0.6,"raise_frequency":0.3,"ev_fold":5.0,"ev_call":9.0,"ev_raise":10.0,"mixed_ev":9.3}]' | Set-Content -LiteralPath (Join-Path $respJob 'combos.json') -Encoding UTF8
          & ./tools/collect_dataset.ps1 -OutputDir $resp -MoneyScale 10
          $r = Import-Csv (Join-Path $resp 'dataset.csv') | Select-Object -First 1
          if ([math]::Abs([double]$r.ev_raise_btn - 1.0) -gt 0.000001) { throw 'BTN response EV scaling failed.' }
          if ([math]::Abs([double]$r.loss_if_fold_btn - 0.5) -gt 0.000001) { throw 'BTN response loss field failed.' }
'''
if 'Test BTN dataset collector schemas' not in ci:
    ci += btn_test
write(ci_rel, ci)

print('BTN study patch applied successfully.')

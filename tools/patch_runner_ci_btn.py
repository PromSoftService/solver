#!/usr/bin/env python3
from pathlib import Path

p = Path('.github/workflows/runner-v013-check.yml')
s = p.read_text(encoding='utf-8-sig')
s = s.replace('name: Runner v013 checks', 'name: Runner v014 checks', 1)

path_anchor = "      - 'scripts/RUN__CFG003__NOD003__BRD001.cmd'\n"
path_extra = (
    "      - 'scripts/Run-CFG003-NOD004-BRD001.ps1'\n"
    "      - 'scripts/Run-CFG003-NOD005-BRD001.ps1'\n"
    "      - 'scripts/RUN__CFG003__NOD004__BRD001.cmd'\n"
    "      - 'scripts/RUN__CFG003__NOD005__BRD001.cmd'\n"
    "      - 'scripts/RUN__CFG003__NOD004_NOD005__BRD001__AND_PUSH.cmd'\n"
)
if 'Run-CFG003-NOD004-BRD001.ps1' not in s:
    if path_anchor not in s:
        raise SystemExit('CI path anchor missing')
    s = s.replace(path_anchor, path_anchor + path_extra, 1)

parse_anchor = "            'scripts/Run-CFG003-NOD003-BRD001.ps1',\n"
if "'scripts/Run-CFG003-NOD004-BRD001.ps1'," not in s:
    if parse_anchor not in s:
        raise SystemExit('CI parser anchor missing')
    s = s.replace(
        parse_anchor,
        parse_anchor
        + "            'scripts/Run-CFG003-NOD004-BRD001.ps1',\n"
        + "            'scripts/Run-CFG003-NOD005-BRD001.ps1',\n",
        1,
    )

if 'Test BTN decision nodes and collector schemas' not in s:
    s += '''

      - name: Test BTN decision nodes and collector schemas
        shell: pwsh
        run: |
          $worker = Get-Content -LiteralPath ./tsgpu-worker.ps1 -Raw
          $batch = Get-Content -LiteralPath ./tsgpu-batch.ps1 -Raw
          $study = Get-Content -LiteralPath ./scripts/Run-Study.ps1 -Raw
          foreach ($node in @('BTN_RESPONSE','BTN_STAB')) {
            foreach ($text in @($worker,$batch,$study)) {
              if ($text -notmatch $node) { throw "$node is missing from runner wiring." }
            }
          }
          if ($worker -notmatch "DecisionNode -eq 'BTN_RESPONSE'") { throw 'Worker does not select BTN response.' }
          if ($worker -notmatch "DecisionNode -eq 'BTN_STAB'") { throw 'Worker does not select BTN stab.' }

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

p.write_text(s, encoding='utf-8')
print('runner CI patched')

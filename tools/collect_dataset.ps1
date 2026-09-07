param(
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
    } elseif ($decisionNode -in @('UTG_CBET', 'UTG_OOP_CBET', 'UTG_RESPONSE')) {
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
            $suffix = if ($actingPlayer -eq 'BTN') { 'btn' } elseif ($actingPlayer -eq 'UTG') { 'utg' } else { 'bb' }
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

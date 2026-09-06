param(
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [double]$MoneyScale = 10.0
)
$ErrorActionPreference = 'Stop'
$rows = New-Object System.Collections.Generic.List[object]
Get-ChildItem -LiteralPath $OutputDir -Directory | Sort-Object Name | ForEach-Object {
    $runPath = Join-Path $_.FullName 'run.json'
    $comboPath = Join-Path $_.FullName 'combos.json'
    if (-not (Test-Path -LiteralPath $runPath) -or -not (Test-Path -LiteralPath $comboPath)) { return }
    $run = Get-Content -LiteralPath $runPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $combos = Get-Content -LiteralPath $comboPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($x in $combos) {
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
        $rows.Add([pscustomobject][ordered]@{
            board = $run.board
            combo = $x.combo
            reach_probability = [double]$x.reach_probability
            fold_frequency = $f
            call_frequency = $c
            raise_frequency = $r
            ev_fold_bb = $evF
            ev_call_bb = $evC
            ev_raise_bb = $evR
            mixed_ev_bb = $mixed
            best_ev_action = $best
            best_ev_bb = $bestEv
            highest_frequency_action = $freqAction
            highest_frequency = $freq
            loss_if_fold_bb = $bestEv - $evF
            loss_if_call_bb = $bestEv - $evC
            loss_if_raise_bb = $bestEv - $evR
            iteration = $run.final_status.iteration
            exploitability = $run.final_status.exploitability
        }) | Out-Null
    }
}
if ($rows.Count -eq 0) { throw 'No */run.json + combos.json pairs found.' }
$out = Join-Path $OutputDir 'dataset.csv'
$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Host "Wrote $($rows.Count) rows -> $out"

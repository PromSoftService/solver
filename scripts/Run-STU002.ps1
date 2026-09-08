[CmdletBinding()]
param([switch]$Resume,[switch]$ShowHostWindow)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

& git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'git fetch failed' }
$head = (& git rev-parse HEAD).Trim()
$remote = (& git rev-parse origin/main).Trim()
if ($head -ne $remote) { throw "Local HEAD $head != origin/main $remote. Synchronize before study." }
$dirty = @(& git status --porcelain --untracked-files=all)
if ($dirty.Count -gt 0) { throw "Working tree is not clean.`n$($dirty -join "`n")" }

. (Join-Path $PSScriptRoot 'Range-Utils.ps1')

$studyPath = Join-Path $root 'studies\STU002__UTG-BB__LEGACY-CFG001-SIZES__FULLTREE__V1.json'
$study = Get-Content $studyPath -Raw -Encoding UTF8 | ConvertFrom-Json
$boardsPath = Join-Path $root $study.board_file
$oopRangePath = Join-Path $root $study.ranges.oop_file
$ipRangePath = Join-Path $root $study.ranges.ip_file
$oopRange = @(Convert-TexasSolverRangeTo1326 -Path $oopRangePath)
$ipRange = @(Convert-TexasSolverRangeTo1326 -Path $ipRangePath)

$effective = [ordered]@{
    runner = [ordered]@{
        maxIterations = [int]$study.solve.max_iterations
        targetExploitability = [double]$study.solve.target_exploitability
    }
    config = [ordered]@{
        oopRange = $oopRange
        ipRange = $ipRange
        startingPot = [double]$study.game.flop_pot_native
        effectiveStack = [double]$study.game.effective_stack_native
        rakeRate = 0
        rakeCap = 0

        oopFlopBet = [string]$study.tree.flop.oop_bet
        ipFlopBet = [string]$study.tree.flop.ip_bet
        oopFlopRaise = [string]$study.tree.flop.oop_raise
        ipFlopRaise = [string]$study.tree.flop.ip_raise

        oopTurnBet = [string]$study.tree.turn.oop_bet
        ipTurnBet = [string]$study.tree.turn.ip_bet
        oopTurnRaise = [string]$study.tree.turn.oop_raise
        ipTurnRaise = [string]$study.tree.turn.ip_raise
        oopTurnDonk = [string]$study.tree.turn.oop_donk

        oopRiverBet = [string]$study.tree.river.oop_bet
        ipRiverBet = [string]$study.tree.river.ip_bet
        oopRiverRaise = [string]$study.tree.river.oop_raise
        ipRiverRaise = [string]$study.tree.river.ip_raise
        oopRiverDonk = [string]$study.tree.river.oop_donk

        maxRaiseNumber = [int]$study.tree.max_raise_number
        addAllinThreshold = [int]$study.tree.add_allin_threshold_percent
        addAllinFlopIp = [bool]$study.tree.add_allin_flop_ip
        addAllinTurnIp = [bool]$study.tree.add_allin_turn_ip
        addAllinRiverIp = [bool]$study.tree.add_allin_river_ip
        addAllinFlopOop = [bool]$study.tree.add_allin_flop_oop
        addAllinTurnOop = [bool]$study.tree.add_allin_turn_oop
        addAllinRiverOop = [bool]$study.tree.add_allin_river_oop
    }
}

[IO.Directory]::CreateDirectory((Join-Path $root '.tmp')) | Out-Null
$tmpConfig = Join-Path $root '.tmp\STU002-effective.json'
$effective | ConvertTo-Json -Depth 100 | Set-Content $tmpConfig -Encoding UTF8

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runName = "STU002__BRD001__RUN-$stamp"
$workDir = Join-Path $root "output\$runName"
if ($Resume) {
    $latest = Get-ChildItem (Join-Path $root 'output') -Directory -Filter 'STU002__BRD001__RUN-*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
    if ($null -eq $latest) { throw 'No incomplete STU002 output found for resume.' }
    $workDir = $latest.FullName
    $runName = $latest.Name
}

& (Join-Path $root 'tsgpu-batch.ps1') -Config $tmpConfig -Boards $boardsPath -OutputDirectory $workDir -Resume:$Resume -ShowHostWindow:$ShowHostWindow

$summary = @(Import-Csv (Join-Path $workDir 'batch-summary.csv'))
if ($summary.Count -ne 286 -or @($summary | Where-Object { $_.status -ne 'done' }).Count -ne 0) {
    throw 'Study validation failed: expected 286 completed boards.'
}
foreach ($row in $summary) {
    $slug = (($row.board -replace '[^0-9A-Za-z]+','_').Trim('_'))
    $boardDir = Join-Path $workDir ('{0:D4}_{1}' -f [int]$row.index,$slug)
    $meta = Get-Content (Join-Path $boardDir 'tree.meta.json') -Raw | ConvertFrom-Json
    if (-not $meta.full_tree_validated) { throw "Invalid full-tree export at $($row.board)" }
}

function Get-Sha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

Copy-Item $studyPath (Join-Path $workDir 'INPUT_STUDY.json')
Copy-Item $boardsPath (Join-Path $workDir 'INPUT_BOARDS.txt')
Copy-Item $oopRangePath (Join-Path $workDir 'INPUT_RANGE_OOP.txt')
Copy-Item $ipRangePath (Join-Path $workDir 'INPUT_RANGE_IP.txt')
Copy-Item $tmpConfig (Join-Path $workDir 'INPUT_EFFECTIVE_CONFIG.json')

$manifest = [ordered]@{
    schema_version = 1
    study_id = 'STU002'
    run_id = $runName
    created_at = (Get-Date).ToString('o')
    board_count = 286
    result_contract = 'one complete validated postflop tree per flop'
    tree_provenance = 'historical CFG001 sizing/action abstraction; full-tree export is the only architectural change'
    git_source_commit = $head
    inputs = [ordered]@{
        study_sha256 = Get-Sha $studyPath
        boards_sha256 = Get-Sha $boardsPath
        oop_range_sha256 = Get-Sha $oopRangePath
        ip_range_sha256 = Get-Sha $ipRangePath
        effective_config_sha256 = Get-Sha $tmpConfig
    }
}
$manifest | ConvertTo-Json -Depth 20 | Set-Content (Join-Path $workDir 'RUN_MANIFEST.json') -Encoding UTF8

$finalDir = Join-Path (Join-Path $root 'results') $runName
if (Test-Path $finalDir) { throw "Result already exists: $finalDir" }
Move-Item $workDir $finalDir

& git add -- "results/$runName"
if ($LASTEXITCODE -ne 0) { throw 'git add result failed' }
& git commit -m "study STU002: legacy CFG001 sizing full-tree BRD001 $stamp"
if ($LASTEXITCODE -ne 0) { throw 'git commit result failed' }
& git pull --rebase origin main
if ($LASTEXITCODE -ne 0) { throw 'git pull --rebase failed; result remains committed locally' }
& git push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw 'git push failed; result remains committed locally' }

Write-Host ''
Write-Host 'STUDY COMPLETE AND PUSHED'
Write-Host "Result: results/$runName"

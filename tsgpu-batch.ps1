[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Config,
    [Parameter(Mandatory = $true, Position = 1)][string]$Boards,
    [Parameter(Mandatory = $true, Position = 2)][string]$OutputDirectory,
    [string]$SolverExe = '',
    [Nullable[int]]$MaxIterations = $null,
    [Nullable[double]]$TargetExploitability = $null,
    [int]$ExpectedBetAmount = 0,
    [int]$ExpectedRaiseAmount = 0,
    [ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET')][string]$DecisionNode = 'BB_RESPONSE',
    [int]$SolveTimeoutMinutes = 180,
    [switch]$ShowHostWindow,
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$configPath = (Resolve-Path -LiteralPath $Config).Path
$boardsPath = (Resolve-Path -LiteralPath $Boards).Path
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($outputPath) | Out-Null

if (-not $SolverExe) {
    $solverCandidates = @(
        $env:TSGPU_SOLVER_EXE,
        (Join-Path $PSScriptRoot '..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),
        (Join-Path $PSScriptRoot 'TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),
        (Join-Path $PSScriptRoot '..\TexasSolverGpu_131.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
    $SolverExe = $solverCandidates | Select-Object -First 1
}
if (-not $SolverExe -or -not (Test-Path -LiteralPath $SolverExe -PathType Leaf)) {
    throw "TexasSolverGpu_131.exe was not found. Put this runner next to TexasSolverGpu-v0.2.0-windows-x64 or pass -SolverExe."
}
$solverPath = (Resolve-Path -LiteralPath $SolverExe).Path

$configDocument = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$configRootProperty = $configDocument.PSObject.Properties['config']
$configRoot = if ($null -ne $configRootProperty) { $configRootProperty.Value } else { $configDocument }

function Read-FirstSetting([string]$Name, [object]$Default) {
    foreach ($containerName in @('runner', 'solve')) {
        $containerProperty = $configDocument.PSObject.Properties[$containerName]
        if ($null -ne $containerProperty -and $null -ne $containerProperty.Value) {
            $valueProperty = $containerProperty.Value.PSObject.Properties[$Name]
            if ($null -ne $valueProperty -and $null -ne $valueProperty.Value) { return $valueProperty.Value }
        }
    }
    $rootProperty = $configRoot.PSObject.Properties[$Name]
    if ($null -ne $rootProperty -and $null -ne $rootProperty.Value) { return $rootProperty.Value }
    return $Default
}

$effectiveMaxIterations = if ($null -ne $MaxIterations) { [int]$MaxIterations } else { [int](Read-FirstSetting 'maxIterations' 1000) }
$effectiveTargetExploitability = if ($null -ne $TargetExploitability) { [double]$TargetExploitability } else { [double](Read-FirstSetting 'targetExploitability' 0.5) }

$boardList = @(Get-Content -LiteralPath $boardsPath -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) { $line }
})
if ($boardList.Count -eq 0) { throw "No boards found in $boardsPath." }

$previousByIndex = @{}
if ($Resume) {
    $previousSummaryPath = Join-Path $outputPath 'batch-summary.csv'
    if (-not (Test-Path -LiteralPath $previousSummaryPath -PathType Leaf)) {
        throw "Resume requested but batch-summary.csv was not found in $outputPath"
    }
    foreach ($row in (Import-Csv -LiteralPath $previousSummaryPath)) {
        $previousByIndex[[int]$row.index] = $row
    }
    Write-Host "Resume mode: preserving completed boards and retrying failed/missing boards."
}

$summary = [System.Collections.Generic.List[object]]::new()
$failed = 0
for ($i = 0; $i -lt $boardList.Count; $i++) {
    $board = $boardList[$i]
    $index = $i + 1
    $slug = ($board -replace '[^0-9A-Za-z]+', '_').Trim('_')
    $jobName = ('{0:D4}_{1}' -f $index, $slug)
    $jobOutput = Join-Path $outputPath $jobName
    $runPath = Join-Path $jobOutput 'run.json'
    $comboPath = Join-Path $jobOutput 'combos.json'

    $previous = if ($previousByIndex.ContainsKey($index)) { $previousByIndex[$index] } else { $null }
    if ($Resume -and $null -ne $previous) {
        if ([string]$previous.board -ne $board) {
            throw "Resume summary board mismatch at index ${index}: expected '$board', found '$($previous.board)'."
        }
        if ([string]$previous.decision_node -ne $DecisionNode) {
            throw "Resume decision-node mismatch at index ${index}: expected '$DecisionNode', found '$($previous.decision_node)'."
        }
        if ([string]$previous.status -eq 'done' -and
            (Test-Path -LiteralPath $runPath -PathType Leaf) -and
            (Test-Path -LiteralPath $comboPath -PathType Leaf)) {
            Write-Host "[$index/$($boardList.Count)] $board (already done)"
            $summary.Add([pscustomobject][ordered]@{
                index = $index
                board = $board
                decision_node = $DecisionNode
                status = 'done'
                output_directory = $jobName
                combos = [int]$previous.combos
                iteration = [int]$previous.iteration
                exploitability = [double]$previous.exploitability
                elapsed_ms = [int]$previous.elapsed_ms
                error = ''
            })
            continue
        }
    }

    if ($Resume -and (Test-Path -LiteralPath $jobOutput)) {
        Remove-Item -LiteralPath $jobOutput -Recurse -Force
    }

    $started = [DateTime]::UtcNow
    Write-Host "[$index/$($boardList.Count)] $board"
    try {
        $oneArguments = @{
            SolverExe = $solverPath
            Config = $configPath
            Board = $board
            OutputDirectory = $jobOutput
            MaxIterations = $effectiveMaxIterations
            TargetExploitability = $effectiveTargetExploitability
            ExpectedBetAmount = $ExpectedBetAmount
            ExpectedRaiseAmount = $ExpectedRaiseAmount
            DecisionNode = $DecisionNode
            SolveTimeoutMinutes = $SolveTimeoutMinutes
            ShowHostWindow = $ShowHostWindow
        }
        & (Join-Path $PSScriptRoot 'tsgpu-worker.ps1') @oneArguments

        if (-not (Test-Path -LiteralPath $runPath)) { throw 'run.json was not created.' }
        $run = Get-Content -LiteralPath $runPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $summary.Add([pscustomobject][ordered]@{
            index = $index
            board = $board
            decision_node = $DecisionNode
            status = 'done'
            output_directory = $jobName
            combos = [int]$run.combo_count
            iteration = [int]$run.final_status.iteration
            exploitability = [double]$run.final_status.exploitability
            elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds
            error = ''
        })
    } catch {
        $failed++
        $summary.Add([pscustomobject][ordered]@{
            index = $index
            board = $board
            decision_node = $DecisionNode
            status = 'error'
            output_directory = $jobName
            combos = 0
            iteration = 0
            exploitability = $null
            elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds
            error = $_.Exception.Message
        })
        Write-Error -ErrorAction Continue "Board $board failed: $($_.Exception.Message)"
    }
}

$summary | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $outputPath 'batch-summary.json') -Encoding UTF8
$summary | Export-Csv -LiteralPath (Join-Path $outputPath 'batch-summary.csv') -NoTypeInformation -Encoding UTF8

Write-Host "Batch complete: $($boardList.Count - $failed) done, $failed failed."
Write-Host "Decision: $DecisionNode"
Write-Host "Summary: $outputPath"
if ($failed -gt 0) { throw "$failed batch job(s) failed." }

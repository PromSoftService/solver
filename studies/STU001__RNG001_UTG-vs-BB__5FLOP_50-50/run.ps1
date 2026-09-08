[CmdletBinding()]
param(
    [string]$OutputDirectory = '',
    [string]$DatasetDirectory = '',
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$studyDirectory = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $studyDirectory '..\..')).Path
$studyName = Split-Path $studyDirectory -Leaf
$configPath = Join-Path $studyDirectory 'config.json'
$boardsPath = Join-Path $studyDirectory 'boards.txt'

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repoRoot "output\$studyName"
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)

$runStamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
if (-not $DatasetDirectory) {
    $DatasetDirectory = Join-Path $repoRoot "datasets\$studyName\$runStamp"
}
$datasetPath = [IO.Path]::GetFullPath($DatasetDirectory)
[IO.Directory]::CreateDirectory($datasetPath) | Out-Null

$commitSha = 'unknown'
try {
    $resolvedSha = (& git -C $repoRoot rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and $resolvedSha) { $commitSha = [string]$resolvedSha }
} catch {}

$started = [DateTime]::UtcNow
$batchArguments = @{
    Config = $configPath
    Boards = $boardsPath
    OutputDirectory = $outputPath
    Resume = $Resume
}
if ($SolverExe) { $batchArguments['SolverExe'] = $SolverExe }

& (Join-Path $repoRoot 'tsgpu-batch.ps1') @batchArguments
$ended = [DateTime]::UtcNow

$summaryJsonPath = Join-Path $outputPath 'batch-summary.json'
$summaryCsvPath = Join-Path $outputPath 'batch-summary.csv'
if (-not (Test-Path -LiteralPath $summaryJsonPath -PathType Leaf)) {
    throw "Missing batch summary: $summaryJsonPath"
}

$parsedSummary = Get-Content -LiteralPath $summaryJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$summary = @($parsedSummary)
$done = @($summary | Where-Object { $_.status -eq 'done' })
$failed = @($summary | Where-Object { $_.status -ne 'done' })
if ($done.Count -ne 5 -or $failed.Count -ne 0) {
    throw "Expected 5/5 successful boards; got $($done.Count) done and $($failed.Count) failed."
}

$requiredFiles = @('run.json', 'node.raw.json', 'combos.json', 'combos.csv', 'bridge-transcript.jsonl')
$validationRows = [System.Collections.Generic.List[object]]::new()
foreach ($row in $done) {
    $boardOutput = Join-Path $outputPath ([string]$row.output_directory)
    $missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $boardOutput $_) -PathType Leaf) })
    if ($missing.Count) {
        throw "Board $($row.board) is missing output files: $($missing -join ', ')"
    }

    $transcript = @(Get-Content -LiteralPath (Join-Path $boardOutput 'bridge-transcript.jsonl') -Encoding UTF8 |
        Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
    $solveStarts = @($transcript | Where-Object { $_.method -eq 'solver.solve.start' }).Count
    $streetExports = @($transcript | Where-Object { $_.method -eq 'solver.export.currentStreet' }).Count
    $forbiddenCalls = @($transcript | Where-Object {
        [string]$_.method -match 'fullTree|allStreets|fullStrategy|dump\.strategy'
    }).Count
    if ($solveStarts -ne 1 -or $streetExports -ne 1 -or $forbiddenCalls -ne 0) {
        throw "Unexpected bridge sequence for $($row.board): solve=$solveStarts export=$streetExports forbidden=$forbiddenCalls"
    }

    $validationRows.Add([pscustomobject][ordered]@{
        board = [string]$row.board
        output_directory = [string]$row.output_directory
        solve_start_calls = $solveStarts
        current_street_export_calls = $streetExports
        forbidden_full_tree_calls = $forbiddenCalls
        output_files = $requiredFiles.Count
        result = 'PASS'
    })
}

$elapsedValues = @($done | ForEach-Object { [double]$_.elapsed_ms } | Sort-Object)
$sumMs = [double](($elapsedValues | Measure-Object -Sum).Sum)
$meanMs = $sumMs / $elapsedValues.Count
$middle = [int][Math]::Floor($elapsedValues.Count / 2)
$medianMs = if (($elapsedValues.Count % 2) -eq 1) {
    $elapsedValues[$middle]
} else {
    ($elapsedValues[$middle - 1] + $elapsedValues[$middle]) / 2
}
$wallMs = [double]($ended - $started).TotalMilliseconds
$estimate286Ms = ($wallMs / $done.Count) * 286

$report = [pscustomobject][ordered]@{
    schema_version = 1
    study_id = 'STU001'
    study_name = $studyName
    source_commit = $commitSha
    started_at_utc = $started.ToString('o')
    ended_at_utc = $ended.ToString('o')
    success = $true
    boards_done = $done.Count
    boards_expected = 5
    decision_node = 'BB_RESPONSE'
    raw_output_path = $outputPath
    dataset_path = $datasetPath
    timing_ms = [pscustomobject][ordered]@{
        total_wall = [int][Math]::Round($wallMs)
        board_sum = [int][Math]::Round($sumMs)
        mean = [int][Math]::Round($meanMs)
        median = [int][Math]::Round($medianMs)
        min = [int][Math]::Round($elapsedValues[0])
        max = [int][Math]::Round($elapsedValues[-1])
        estimate_286 = [int][Math]::Round($estimate286Ms)
    }
    validation = [pscustomobject][ordered]@{
        required_files_per_board = $requiredFiles.Count
        exactly_one_solve_start_per_board = $true
        exactly_one_current_street_export_per_board = $true
        forbidden_full_tree_calls = 0
    }
    errors = @()
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $datasetPath 'timing-report.json') -Encoding UTF8
$validationRows | Export-Csv -LiteralPath (Join-Path $datasetPath 'validation.csv') -NoTypeInformation -Encoding UTF8
Copy-Item -LiteralPath $summaryJsonPath -Destination (Join-Path $datasetPath 'batch-summary.json')
Copy-Item -LiteralPath $summaryCsvPath -Destination (Join-Path $datasetPath 'batch-summary.csv')

$reportText = @"
# STU001 five-flop result

- Success: 5/5
- Source commit: $commitSha
- Decision: BB_RESPONSE after UTG 50% flop bet
- Total wall time: $([Math]::Round($wallMs / 1000, 3)) s
- Mean per board: $([Math]::Round($meanMs / 1000, 3)) s
- Median per board: $([Math]::Round($medianMs / 1000, 3)) s
- Minimum: $([Math]::Round($elapsedValues[0] / 1000, 3)) s
- Maximum: $([Math]::Round($elapsedValues[-1] / 1000, 3)) s
- Estimated 286-board runtime: $([Math]::Round($estimate286Ms / 60000, 2)) min
- Raw output: $outputPath
- Errors: none
"@
$reportText | Set-Content -LiteralPath (Join-Path $datasetPath 'README.md') -Encoding UTF8

Write-Host "STUDY COMPLETE: 5/5"
Write-Host "Total wall: $([Math]::Round($wallMs / 1000, 3)) s"
Write-Host "Dataset: $datasetPath"

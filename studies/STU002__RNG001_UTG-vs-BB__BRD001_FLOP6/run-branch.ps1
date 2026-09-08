[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('01_BB_FIRST', '02_UTG_AFTER_CHECK', '03_BB_AFTER_CBET', '04_UTG_AFTER_CHECK_RAISE', '05_UTG_AFTER_DONK', '06_BB_AFTER_DONK_RAISE')]
    [string]$BranchId,
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
$boardsPath = Join-Path $repoRoot 'boards\BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt'
$study = Get-Content -LiteralPath (Join-Path $studyDirectory 'study.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$branch = @($study.branches | Where-Object { $_.id -eq $BranchId })
if ($branch.Count -ne 1) { throw "Branch '$BranchId' is not uniquely defined." }
$branch = $branch[0]

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repoRoot "output\$studyName\$BranchId"
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $Resume -and (Test-Path -LiteralPath $outputPath)) {
    throw "Output already exists: $outputPath. Use -Resume or select another -OutputDirectory."
}

$runStamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
if (-not $DatasetDirectory) {
    $DatasetDirectory = Join-Path $repoRoot "datasets\$studyName\$BranchId\$runStamp"
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
    DecisionNode = [string]$branch.decision_node
    ExpectedBetAmount = [int]$branch.expected_bet_amount
    ExpectedRaiseAmount = [int]$branch.expected_raise_amount
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
if ($done.Count -ne 286 -or $failed.Count -ne 0) {
    throw "Expected 286/286 successful boards; got $($done.Count) done and $($failed.Count) failed."
}

$requiredFiles = @('run.json', 'node.raw.json', 'combos.json', 'combos.csv', 'bridge-transcript.jsonl')
$validationRows = [System.Collections.Generic.List[object]]::new()
$aggregatePath = Join-Path $datasetPath 'combos.csv'
$aggregateStarted = $false
foreach ($row in $done) {
    $boardOutput = Join-Path $outputPath ([string]$row.output_directory)
    $missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $boardOutput $_) -PathType Leaf) })
    if ($missing.Count) {
        throw "Board $($row.board) is missing output files: $($missing -join ', ')"
    }

    $run = Get-Content -LiteralPath (Join-Path $boardOutput 'run.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([string]$run.decision_node -ne [string]$branch.decision_node) {
        throw "Board $($row.board) exported $($run.decision_node), expected $($branch.decision_node)."
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
        decision_node = [string]$run.decision_node
        acting_player = [string]$run.acting_player
        actions = @($run.node_actions) -join ' / '
        combos = [int]$run.combo_count
        solve_start_calls = $solveStarts
        current_street_export_calls = $streetExports
        forbidden_full_tree_calls = $forbiddenCalls
        result = 'PASS'
    })

    $enrichedCombos = @(Import-Csv -LiteralPath (Join-Path $boardOutput 'combos.csv') | ForEach-Object {
        $item = [ordered]@{
            board = [string]$row.board
            board_index = [int]$row.index
            decision_node = [string]$branch.decision_node
            acting_player = [string]$branch.acting_player
        }
        foreach ($property in $_.PSObject.Properties) { $item[$property.Name] = $property.Value }
        [pscustomobject]$item
    })
    if (-not $aggregateStarted) {
        $enrichedCombos | Export-Csv -LiteralPath $aggregatePath -NoTypeInformation -Encoding UTF8
        $aggregateStarted = $true
    } else {
        $enrichedCombos | Export-Csv -LiteralPath $aggregatePath -NoTypeInformation -Encoding UTF8 -Append
    }
}

$elapsedValues = @($done | ForEach-Object { [double]$_.elapsed_ms } | Sort-Object)
$sumMs = [double](($elapsedValues | Measure-Object -Sum).Sum)
$meanMs = $sumMs / $elapsedValues.Count
$middle = [int][Math]::Floor($elapsedValues.Count / 2)
$medianMs = ($elapsedValues[$middle - 1] + $elapsedValues[$middle]) / 2
$wallMs = [double]($ended - $started).TotalMilliseconds

$report = [pscustomobject][ordered]@{
    schema_version = 1
    study_id = 'STU002'
    branch_id = $BranchId
    decision_node = [string]$branch.decision_node
    acting_player = [string]$branch.acting_player
    history = [string]$branch.history
    actions = [string]$branch.actions
    source_commit = $commitSha
    started_at_utc = $started.ToString('o')
    ended_at_utc = $ended.ToString('o')
    success = $true
    boards_done = $done.Count
    boards_expected = 286
    raw_output_path = $outputPath
    dataset_path = $datasetPath
    timing_ms = [pscustomobject][ordered]@{
        total_wall = [int][Math]::Round($wallMs)
        board_sum = [int][Math]::Round($sumMs)
        mean = [int][Math]::Round($meanMs)
        median = [int][Math]::Round($medianMs)
        min = [int][Math]::Round($elapsedValues[0])
        max = [int][Math]::Round($elapsedValues[-1])
    }
    validation = [pscustomobject][ordered]@{
        required_files_per_board = $requiredFiles.Count
        exactly_one_solve_start_per_board = $true
        exactly_one_current_street_export_per_board = $true
        forbidden_full_tree_calls = 0
        aggregate_combo_csv = $true
    }
    errors = @()
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $datasetPath 'timing-report.json') -Encoding UTF8
$validationRows | Export-Csv -LiteralPath (Join-Path $datasetPath 'validation.csv') -NoTypeInformation -Encoding UTF8
Copy-Item -LiteralPath $summaryJsonPath -Destination (Join-Path $datasetPath 'batch-summary.json')
Copy-Item -LiteralPath $summaryCsvPath -Destination (Join-Path $datasetPath 'batch-summary.csv')

$reportText = @"
# STU002 $BranchId result

- Success: 286/286
- Source commit: $commitSha
- Decision: $($branch.decision_node) ($($branch.acting_player))
- History: $($branch.history)
- Actions: $($branch.actions)
- Total wall time: $([Math]::Round($wallMs / 60000, 2)) min
- Mean per board: $([Math]::Round($meanMs / 1000, 3)) s
- Median per board: $([Math]::Round($medianMs / 1000, 3)) s
- Minimum: $([Math]::Round($elapsedValues[0] / 1000, 3)) s
- Maximum: $([Math]::Round($elapsedValues[-1] / 1000, 3)) s
- Raw output: $outputPath
- Aggregate combos: $aggregatePath
- Errors: none
"@
$reportText | Set-Content -LiteralPath (Join-Path $datasetPath 'README.md') -Encoding UTF8

Write-Host "STUDY BRANCH COMPLETE: $BranchId 286/286"
Write-Host "Total wall: $([Math]::Round($wallMs / 60000, 2)) min"
Write-Host "Dataset: $datasetPath"

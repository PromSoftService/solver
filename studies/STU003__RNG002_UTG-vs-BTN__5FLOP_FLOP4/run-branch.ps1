[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('01_UTG_FIRST', '02_BTN_AFTER_CHECK', '03_BTN_AFTER_CBET', '04_UTG_AFTER_STAB')]
    [string]$BranchId,
    [string]$OutputDirectory = '',
    [string]$DatasetDirectory = '',
    [string]$SolverExe = '',
    [string]$StudyDirectory = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$operationStarted = [DateTime]::UtcNow

$studyDirectory = if ($StudyDirectory) { [IO.Path]::GetFullPath($StudyDirectory) } else { $PSScriptRoot }
$repoRoot = (Resolve-Path (Join-Path $studyDirectory '..\..')).Path
$studyName = Split-Path $studyDirectory -Leaf
$configPath = Join-Path $studyDirectory 'config.json'
$study = Get-Content -LiteralPath (Join-Path $studyDirectory 'study.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$boardsPath = if ($study.board_file) {
    Join-Path $repoRoot ([string]$study.board_file)
} else {
    Join-Path $studyDirectory 'boards.txt'
}
$branch = @($study.branches | Where-Object { $_.id -eq $BranchId })
if ($branch.Count -ne 1) { throw "Branch '$BranchId' is not uniquely defined." }
$branch = $branch[0]

$boardList = @(Get-Content -LiteralPath $boardsPath -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) { $line }
})
$expectedBoards = $boardList.Count
if ($study.expected_boards -and $expectedBoards -ne [int]$study.expected_boards) {
    throw "$($study.study_id) requires $($study.expected_boards) boards; got $expectedBoards."
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repoRoot "output\$studyName\$BranchId"
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $Resume -and (Test-Path -LiteralPath $outputPath)) {
    throw "Output already exists: $outputPath. Use -Resume or select another -OutputDirectory."
}

$runStamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
if (-not $DatasetDirectory) {
    $DatasetDirectory = Join-Path $repoRoot "datasets\$studyName\$runStamp\$BranchId"
}
$datasetPath = [IO.Path]::GetFullPath($DatasetDirectory)
[IO.Directory]::CreateDirectory($datasetPath) | Out-Null

$commitSha = 'unknown'
try {
    $resolvedSha = (& git -C $repoRoot rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and $resolvedSha) { $commitSha = [string]$resolvedSha }
} catch {}

$batchStarted = [DateTime]::UtcNow
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
$batchEnded = [DateTime]::UtcNow

$summaryJsonPath = Join-Path $outputPath 'batch-summary.json'
$summaryCsvPath = Join-Path $outputPath 'batch-summary.csv'
if (-not (Test-Path -LiteralPath $summaryJsonPath -PathType Leaf)) {
    throw "Missing batch summary: $summaryJsonPath"
}

$parsedSummary = Get-Content -LiteralPath $summaryJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$summary = @($parsedSummary)
$done = @($summary | Where-Object { $_.status -eq 'done' })
$failed = @($summary | Where-Object { $_.status -ne 'done' })
if ($done.Count -ne $expectedBoards -or $failed.Count -ne 0) {
    throw "Expected $expectedBoards/$expectedBoards successful boards; got $($done.Count) done and $($failed.Count) failed."
}

$requiredFiles = @('run.json', 'node.raw.json', 'combos.json', 'combos.csv', 'bridge-transcript.jsonl')
$validationRows = [System.Collections.Generic.List[object]]::new()
$aggregatePath = Join-Path $datasetPath 'combos.csv'
$aggregateStarted = $false
$previousCulture = [Threading.Thread]::CurrentThread.CurrentCulture
try {
    [Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
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

        $parsedCombos = Get-Content -LiteralPath (Join-Path $boardOutput 'combos.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $comboSource = @($parsedCombos)
        if ($comboSource.Count -ne [int]$run.combo_count) {
            throw "Board $($row.board) combo count mismatch: JSON=$($comboSource.Count), run=$($run.combo_count)."
        }
        $enrichedCombos = @($comboSource | ForEach-Object {
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
} finally {
    [Threading.Thread]::CurrentThread.CurrentCulture = $previousCulture
}

$validationRows | Export-Csv -LiteralPath (Join-Path $datasetPath 'validation.csv') -NoTypeInformation -Encoding UTF8
Copy-Item -LiteralPath $summaryJsonPath -Destination (Join-Path $datasetPath 'batch-summary.json')
Copy-Item -LiteralPath $summaryCsvPath -Destination (Join-Path $datasetPath 'batch-summary.csv')

$elapsedValues = @($done | ForEach-Object { [double]$_.elapsed_ms } | Sort-Object)
$sumMs = [double](($elapsedValues | Measure-Object -Sum).Sum)
$meanMs = $sumMs / $elapsedValues.Count
$middle = [int][Math]::Floor($elapsedValues.Count / 2)
$medianMs = if (($elapsedValues.Count % 2) -eq 1) {
    $elapsedValues[$middle]
} else {
    ($elapsedValues[$middle - 1] + $elapsedValues[$middle]) / 2
}
$operationEnded = [DateTime]::UtcNow
$operationWallMs = [double]($operationEnded - $operationStarted).TotalMilliseconds
$batchWallMs = [double]($batchEnded - $batchStarted).TotalMilliseconds
$postprocessWallMs = [Math]::Max(0.0, $operationWallMs - $batchWallMs)

$report = [pscustomobject][ordered]@{
    schema_version = 1
    study_id = [string]$study.study_id
    branch_id = $BranchId
    decision_node = [string]$branch.decision_node
    acting_player = [string]$branch.acting_player
    history = [string]$branch.history
    actions = [string]$branch.actions
    source_commit = $commitSha
    started_at_utc = $operationStarted.ToString('o')
    ended_at_utc = $operationEnded.ToString('o')
    resumed = [bool]$Resume
    success = $true
    boards_done = $done.Count
    boards_expected = $expectedBoards
    raw_output_path = $outputPath
    dataset_path = $datasetPath
    timing_ms = [pscustomobject][ordered]@{
        operation_total_wall_including_parsing = [int][Math]::Round($operationWallMs)
        solver_batch_wall = [int][Math]::Round($batchWallMs)
        validation_and_parsing_wall = [int][Math]::Round($postprocessWallMs)
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

$reportText = @"
# $($study.study_id) $BranchId result

- Success: $expectedBoards/$expectedBoards
- Source commit: $commitSha
- Decision: $($branch.decision_node) ($($branch.acting_player))
- History: $($branch.history)
- Actions: $($branch.actions)
- Total branch wall time including validation/parsing: $([Math]::Round($operationWallMs / 1000, 3)) s
- Solver batch wall time: $([Math]::Round($batchWallMs / 1000, 3)) s
- Validation/parsing wall time: $([Math]::Round($postprocessWallMs / 1000, 3)) s
- Mean per board: $([Math]::Round($meanMs / 1000, 3)) s
- Raw output: $outputPath
- Aggregate combos: $aggregatePath
- Errors: none
"@
$reportText | Set-Content -LiteralPath (Join-Path $datasetPath 'README.md') -Encoding UTF8

Write-Host "$($study.study_id) BRANCH COMPLETE: $BranchId $expectedBoards/$expectedBoards"
Write-Host "Branch total including parsing: $([Math]::Round($operationWallMs / 1000, 3)) s"
Write-Host "Dataset: $datasetPath"

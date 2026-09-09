[CmdletBinding()]
param(
    [string]$OutputRoot = '',
    [string]$DatasetRoot = '',
    [string]$SolverExe = '',
    [string]$StudyDirectory = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$operationStarted = [DateTime]::UtcNow
$operationTimer = [Diagnostics.Stopwatch]::StartNew()

$studyDirectory = if ($StudyDirectory) { [IO.Path]::GetFullPath($StudyDirectory) } else { $PSScriptRoot }
$repoRoot = (Resolve-Path (Join-Path $studyDirectory '..\..')).Path
$studyName = Split-Path $studyDirectory -Leaf
$study = Get-Content -LiteralPath (Join-Path $studyDirectory 'study.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$boardsPath = if ($study.board_file) {
    Join-Path $repoRoot ([string]$study.board_file)
} else {
    Join-Path $studyDirectory 'boards.txt'
}
$boardCount = @(Get-Content -LiteralPath $boardsPath -Encoding UTF8 | Where-Object {
    $_.Trim() -and -not $_.Trim().StartsWith('#')
}).Count
if ($study.expected_boards -and $boardCount -ne [int]$study.expected_boards) {
    throw "$($study.study_id) requires $($study.expected_boards) boards; got $boardCount."
}
$runStamp = $operationStarted.ToString('yyyyMMdd-HHmmssZ')
if (-not $OutputRoot) { $OutputRoot = Join-Path $repoRoot "output\$studyName" }
if (-not $DatasetRoot) { $DatasetRoot = Join-Path $repoRoot "datasets\$studyName\$runStamp" }
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
$datasetPath = [IO.Path]::GetFullPath($DatasetRoot)
[IO.Directory]::CreateDirectory($datasetPath) | Out-Null

$branchIds = @($study.branches | ForEach-Object { [string]$_.id })
$branchRows = [System.Collections.Generic.List[object]]::new()
$caughtError = $null

Write-Host "$($study.study_id) OPERATION START: $($operationStarted.ToString('o'))"
Write-Host "Scope: $($branchIds.Count) branches x $boardCount flops = $($branchIds.Count * $boardCount) solves"

try {
    foreach ($branchId in $branchIds) {
        Write-Host ""
        Write-Host "[$($branchRows.Count + 1)/$($branchIds.Count)] Starting $branchId; total elapsed $([Math]::Round($operationTimer.Elapsed.TotalSeconds, 3)) s"
        $branchOutputPath = Join-Path $outputPath $branchId
        $branchDatasetPath = Join-Path $datasetPath $branchId
        $branchCanResume = $Resume -and (Test-Path -LiteralPath (Join-Path $branchOutputPath 'batch-summary.csv') -PathType Leaf)
        if ($Resume -and -not $branchCanResume -and (Test-Path -LiteralPath $branchOutputPath)) {
            $staleItems = @(Get-ChildItem -LiteralPath $branchOutputPath -Force)
            if ($staleItems.Count -eq 0) {
                Remove-Item -LiteralPath $branchOutputPath
            } else {
                throw "Cannot safely start ${branchId}: output exists without batch-summary.csv and is not empty: $branchOutputPath"
            }
        }
        $arguments = @{
            BranchId = $branchId
            OutputDirectory = $branchOutputPath
            DatasetDirectory = $branchDatasetPath
            StudyDirectory = $studyDirectory
        }
        if ($branchCanResume) { $arguments['Resume'] = $true }
        if ($SolverExe) { $arguments['SolverExe'] = $SolverExe }
        & (Join-Path $PSScriptRoot 'run-branch.ps1') @arguments

        $branchReport = Get-Content -LiteralPath (Join-Path $datasetPath "$branchId\timing-report.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        $branchRows.Add([pscustomobject][ordered]@{
            branch_id = $branchId
            decision_node = [string]$branchReport.decision_node
            boards_done = [int]$branchReport.boards_done
            elapsed_ms_including_parsing = [int]$branchReport.timing_ms.operation_total_wall_including_parsing
            result = 'PASS'
        })
        Write-Host "Completed $branchId; total elapsed $([Math]::Round($operationTimer.Elapsed.TotalSeconds, 3)) s"
    }
} catch {
    $caughtError = $_
} finally {
    $operationTimer.Stop()
    $operationEnded = [DateTime]::UtcNow
    $success = $null -eq $caughtError
    $errorText = if ($success) { '' } else { [string]$caughtError.Exception.Message }
    $completedBoards = if ($branchRows.Count) {
        [int](($branchRows | Measure-Object -Property boards_done -Sum).Sum)
    } else {
        0
    }
    $report = [pscustomobject][ordered]@{
        schema_version = 1
        study_id = [string]$study.study_id
        operation = "$($branchIds.Count) branches by $boardCount flops, including validation and parsing"
        started_at_utc = $operationStarted.ToString('o')
        ended_at_utc = $operationEnded.ToString('o')
        success = $success
        resumed = [bool]$Resume
        branches_expected = $branchIds.Count
        branches_completed = $branchRows.Count
        boards_expected_total = $branchIds.Count * $boardCount
        boards_completed_total = $completedBoards
        total_wall_ms_including_all_parsing = [int][Math]::Round($operationTimer.Elapsed.TotalMilliseconds)
        raw_output_root = $outputPath
        dataset_root = $datasetPath
        branches = @($branchRows)
        error = $errorText
    }
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $datasetPath 'operation-timing.json') -Encoding UTF8
    $branchRows | Export-Csv -LiteralPath (Join-Path $datasetPath 'branches.csv') -NoTypeInformation -Encoding UTF8

    Write-Host ""
    Write-Host "$($study.study_id) OPERATION END: $($operationEnded.ToString('o'))"
    Write-Host "Total elapsed including all parsing: $([Math]::Round($operationTimer.Elapsed.TotalSeconds, 3)) s"
    Write-Host "Completed branches: $($branchRows.Count)/$($branchIds.Count)"
    Write-Host "Operation report: $(Join-Path $datasetPath 'operation-timing.json')"
}

if ($null -ne $caughtError) { throw $caughtError }

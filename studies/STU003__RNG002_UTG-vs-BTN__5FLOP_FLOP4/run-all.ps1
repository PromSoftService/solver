[CmdletBinding()]
param(
    [string]$OutputRoot = '',
    [string]$DatasetRoot = '',
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$operationStarted = [DateTime]::UtcNow
$operationTimer = [Diagnostics.Stopwatch]::StartNew()

$studyDirectory = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $studyDirectory '..\..')).Path
$studyName = Split-Path $studyDirectory -Leaf
$runStamp = $operationStarted.ToString('yyyyMMdd-HHmmssZ')
if (-not $OutputRoot) { $OutputRoot = Join-Path $repoRoot "output\$studyName" }
if (-not $DatasetRoot) { $DatasetRoot = Join-Path $repoRoot "datasets\$studyName\$runStamp" }
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
$datasetPath = [IO.Path]::GetFullPath($DatasetRoot)
[IO.Directory]::CreateDirectory($datasetPath) | Out-Null

$branchIds = @(
    '01_UTG_FIRST',
    '02_BTN_AFTER_CHECK',
    '03_BTN_AFTER_CBET',
    '04_UTG_AFTER_STAB'
)
$branchRows = [System.Collections.Generic.List[object]]::new()
$caughtError = $null

Write-Host "STU003 OPERATION START: $($operationStarted.ToString('o'))"
Write-Host "Scope: $($branchIds.Count) branches x 5 flops = $($branchIds.Count * 5) solves"

try {
    foreach ($branchId in $branchIds) {
        Write-Host ""
        Write-Host "[$($branchRows.Count + 1)/$($branchIds.Count)] Starting $branchId; total elapsed $([Math]::Round($operationTimer.Elapsed.TotalSeconds, 3)) s"
        $arguments = @{
            BranchId = $branchId
            OutputDirectory = (Join-Path $outputPath $branchId)
            DatasetDirectory = (Join-Path $datasetPath $branchId)
            Resume = $Resume
        }
        if ($SolverExe) { $arguments['SolverExe'] = $SolverExe }
        & (Join-Path $studyDirectory 'run-branch.ps1') @arguments

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
    $report = [pscustomobject][ordered]@{
        schema_version = 1
        study_id = 'STU003'
        operation = 'four branches by five flops, including validation and parsing'
        started_at_utc = $operationStarted.ToString('o')
        ended_at_utc = $operationEnded.ToString('o')
        success = $success
        resumed = [bool]$Resume
        branches_expected = $branchIds.Count
        branches_completed = $branchRows.Count
        boards_expected_total = $branchIds.Count * 5
        boards_completed_total = [int](($branchRows | Measure-Object -Property boards_done -Sum).Sum)
        total_wall_ms_including_all_parsing = [int][Math]::Round($operationTimer.Elapsed.TotalMilliseconds)
        raw_output_root = $outputPath
        dataset_root = $datasetPath
        branches = @($branchRows)
        error = $errorText
    }
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $datasetPath 'operation-timing.json') -Encoding UTF8
    $branchRows | Export-Csv -LiteralPath (Join-Path $datasetPath 'branches.csv') -NoTypeInformation -Encoding UTF8

    Write-Host ""
    Write-Host "STU003 OPERATION END: $($operationEnded.ToString('o'))"
    Write-Host "Total elapsed including all parsing: $([Math]::Round($operationTimer.Elapsed.TotalSeconds, 3)) s"
    Write-Host "Completed branches: $($branchRows.Count)/$($branchIds.Count)"
    Write-Host "Operation report: $(Join-Path $datasetPath 'operation-timing.json')"
}

if ($null -ne $caughtError) { throw $caughtError }

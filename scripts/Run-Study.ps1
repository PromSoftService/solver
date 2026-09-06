[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RangeId,
    [Parameter(Mandatory = $true)][string]$ConfigId,
    [Parameter(Mandatory = $true)][string]$BoardSetId,
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [Parameter(Mandatory = $true)][string]$BoardsPath,
    [Parameter(Mandatory = $true)][string]$RangeProfilePath,
    [Parameter(Mandatory = $true)][string]$UtgRangePath,
    [Parameter(Mandatory = $true)][string]$BbRangePath,
    [int]$ExpectedBetAmount = 0,
    [int]$ExpectedRaiseAmount = 0,
    [double]$MoneyScale = 10.0
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

function Resolve-StudyPath([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) {
        return (Resolve-Path -LiteralPath $Path).Path
    }
    return (Resolve-Path -LiteralPath (Join-Path $root $Path)).Path
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$configPathAbs = Resolve-StudyPath $ConfigPath
$boardsPathAbs = Resolve-StudyPath $BoardsPath
$rangeProfilePathAbs = Resolve-StudyPath $RangeProfilePath
$utgRangePathAbs = Resolve-StudyPath $UtgRangePath
$bbRangePathAbs = Resolve-StudyPath $BbRangePath

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runName = "OUT__${RangeId}__${ConfigId}__${BoardSetId}__RUN-${timestamp}"
$outputRoot = Join-Path $root 'output'
$datasetsRoot = Join-Path $root 'datasets'
$outputDir = Join-Path $outputRoot $runName

[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
[IO.Directory]::CreateDirectory($datasetsRoot) | Out-Null

$boards = @(Get-Content -LiteralPath $boardsPathAbs -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) { $line }
})
if ($boards.Count -eq 0) { throw "No boards found in $boardsPathAbs" }

Write-Host ''
Write-Host '============================================================'
Write-Host "RANGE : $RangeId"
Write-Host "CONFIG: $ConfigId"
Write-Host "BOARDS: $BoardSetId ($($boards.Count))"
Write-Host "OUTPUT: $outputDir"
Write-Host '============================================================'
Write-Host ''

$batchArgs = @{
    Config = $configPathAbs
    Boards = $boardsPathAbs
    OutputDirectory = $outputDir
    ExpectedBetAmount = $ExpectedBetAmount
    ExpectedRaiseAmount = $ExpectedRaiseAmount
}
& (Join-Path $root 'tsgpu-batch.ps1') @batchArgs

Write-Host ''
Write-Host 'Building analysis dataset...'
& (Join-Path $root 'tools\collect_dataset.ps1') -OutputDir $outputDir -MoneyScale $MoneyScale

Copy-Item -LiteralPath $configPathAbs -Destination (Join-Path $outputDir 'INPUT_CONFIG.json') -Force
Copy-Item -LiteralPath $boardsPathAbs -Destination (Join-Path $outputDir 'INPUT_BOARDS.txt') -Force
Copy-Item -LiteralPath $rangeProfilePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_PROFILE.json') -Force
Copy-Item -LiteralPath $utgRangePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_UTG.txt') -Force
Copy-Item -LiteralPath $bbRangePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_BB.txt') -Force

$versionPath = Join-Path $root 'VERSION-v012.txt'
if (Test-Path -LiteralPath $versionPath) {
    Copy-Item -LiteralPath $versionPath -Destination (Join-Path $outputDir 'RUNNER_VERSION.txt') -Force
}

$datasetSource = Join-Path $outputDir 'dataset.csv'
if (-not (Test-Path -LiteralPath $datasetSource -PathType Leaf)) {
    throw 'dataset.csv was not created.'
}

$datasetName = "DS__${RangeId}__${ConfigId}__${BoardSetId}__RUN-${timestamp}.csv"
$datasetPath = Join-Path $datasetsRoot $datasetName
Copy-Item -LiteralPath $datasetSource -Destination $datasetPath -Force

$manifest = [ordered]@{
    schema_version = 1
    run_id = $runName
    created_at = (Get-Date).ToString('o')
    range_id = $RangeId
    config_id = $ConfigId
    board_set_id = $BoardSetId
    board_count = $boards.Count
    money_scale = $MoneyScale
    expected_bet_amount = $ExpectedBetAmount
    expected_raise_amount = $ExpectedRaiseAmount
    inputs = [ordered]@{
        config = [ordered]@{ file = [IO.Path]::GetFileName($configPathAbs); sha256 = Get-Sha256 $configPathAbs }
        boards = [ordered]@{ file = [IO.Path]::GetFileName($boardsPathAbs); sha256 = Get-Sha256 $boardsPathAbs }
        range_profile = [ordered]@{ file = [IO.Path]::GetFileName($rangeProfilePathAbs); sha256 = Get-Sha256 $rangeProfilePathAbs }
        utg_range = [ordered]@{ file = [IO.Path]::GetFileName($utgRangePathAbs); sha256 = Get-Sha256 $utgRangePathAbs }
        bb_range = [ordered]@{ file = [IO.Path]::GetFileName($bbRangePathAbs); sha256 = Get-Sha256 $bbRangePathAbs }
    }
    artifacts = [ordered]@{
        raw_output_directory = $runName
        dataset = $datasetName
    }
}

$manifestJson = $manifest | ConvertTo-Json -Depth 10
$manifestPath = Join-Path $outputDir 'RUN_MANIFEST.json'
$manifestJson | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifestJson | Set-Content -LiteralPath (Join-Path $datasetsRoot ($datasetName -replace '\.csv$', '.manifest.json')) -Encoding UTF8

Write-Host ''
Write-Host '============================================================'
Write-Host 'DONE'
Write-Host "Raw output: $outputDir"
Write-Host "Dataset   : $datasetPath"
Write-Host '============================================================'

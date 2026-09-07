[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RangeId,
    [Parameter(Mandatory = $true)][string]$ConfigId,
    [Parameter(Mandatory = $true)][string]$BoardSetId,
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [Parameter(Mandatory = $true)][string]$BoardsPath,
    [Parameter(Mandatory = $true)][string]$RangeProfilePath,
    [string]$UtgRangePath = '',
    [string]$BbRangePath = '',
    [string]$OopRangePath = '',
    [string]$IpRangePath = '',
    [string]$OopPosition = '',
    [string]$IpPosition = '',
    [ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET', 'BTN_RESPONSE', 'BTN_STAB', 'UTG_RESPONSE')][string]$DecisionNode = 'BB_RESPONSE',
    [string]$DecisionId = '',
    [int]$ExpectedBetAmount = 0,
    [int]$ExpectedRaiseAmount = 0,
    [double]$MoneyScale = 10.0,
    [string]$ResumeOutputDirectory = ''
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

$usingGenericRanges = [bool]($OopRangePath -or $IpRangePath -or $OopPosition -or $IpPosition)
if ($usingGenericRanges) {
    if (-not $OopRangePath -or -not $IpRangePath -or -not $OopPosition -or -not $IpPosition) {
        throw 'Generic range mode requires OopRangePath, IpRangePath, OopPosition and IpPosition together.'
    }
    $oopRangePathAbs = Resolve-StudyPath $OopRangePath
    $ipRangePathAbs = Resolve-StudyPath $IpRangePath
} else {
    if (-not $UtgRangePath -or -not $BbRangePath) {
        throw 'Legacy range mode requires UtgRangePath and BbRangePath.'
    }
    # Existing RNG001 studies are BB OOP and UTG IP.
    $oopRangePathAbs = Resolve-StudyPath $BbRangePath
    $ipRangePathAbs = Resolve-StudyPath $UtgRangePath
    $OopPosition = 'BB'
    $IpPosition = 'UTG'
}

$OopPosition = $OopPosition.ToUpperInvariant()
$IpPosition = $IpPosition.ToUpperInvariant()
if ($OopPosition -eq $IpPosition) { throw 'OOP and IP positions must be different.' }

$idParts = @($RangeId, $ConfigId)
if ($DecisionId) { $idParts += $DecisionId }
$idParts += $BoardSetId
$idStem = $idParts -join '__'
$outputRoot = Join-Path $root 'output'
$datasetsRoot = Join-Path $root 'datasets'
[IO.Directory]::CreateDirectory($outputRoot) | Out-Null
[IO.Directory]::CreateDirectory($datasetsRoot) | Out-Null

$resuming = [bool]$ResumeOutputDirectory
if ($resuming) {
    $outputDir = [IO.Path]::GetFullPath($ResumeOutputDirectory)
    if (-not (Test-Path -LiteralPath $outputDir -PathType Container)) {
        throw "Resume output directory does not exist: $outputDir"
    }
    $runName = Split-Path -Leaf $outputDir
    $expectedPrefix = "OUT__${idStem}__RUN-"
    if (-not $runName.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Resume output '$runName' does not match study '$idStem'."
    }
    $timestamp = $runName.Substring($expectedPrefix.Length)
    if (-not $timestamp) { throw "Cannot recover run timestamp from $runName" }
} else {
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $runName = "OUT__${idStem}__RUN-${timestamp}"
    $outputDir = Join-Path $outputRoot $runName
}

$boards = @(Get-Content -LiteralPath $boardsPathAbs -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) { $line }
})
if ($boards.Count -eq 0) { throw "No boards found in $boardsPathAbs" }

Write-Host ''
Write-Host '============================================================'
Write-Host "RANGE   : $RangeId"
Write-Host "CONFIG  : $ConfigId"
if ($DecisionId) { Write-Host "DECISION: $DecisionId ($DecisionNode)" } else { Write-Host "DECISION: $DecisionNode" }
Write-Host "PLAYERS : $OopPosition OOP / $IpPosition IP"
Write-Host "BOARDS  : $BoardSetId ($($boards.Count))"
Write-Host "OUTPUT  : $outputDir"
if ($resuming) { Write-Host 'MODE    : RESUME FAILED/MISSING BOARDS' }
Write-Host '============================================================'
Write-Host ''

$batchArgs = @{
    Config = $configPathAbs
    Boards = $boardsPathAbs
    OutputDirectory = $outputDir
    ExpectedBetAmount = $ExpectedBetAmount
    ExpectedRaiseAmount = $ExpectedRaiseAmount
    DecisionNode = $DecisionNode
}
if ($resuming) { $batchArgs['Resume'] = $true }
& (Join-Path $root 'tsgpu-batch.ps1') @batchArgs

Write-Host ''
Write-Host 'Building analysis dataset...'
& (Join-Path $root 'tools\collect_dataset.ps1') -OutputDir $outputDir -MoneyScale $MoneyScale

Copy-Item -LiteralPath $configPathAbs -Destination (Join-Path $outputDir 'INPUT_CONFIG.json') -Force
Copy-Item -LiteralPath $boardsPathAbs -Destination (Join-Path $outputDir 'INPUT_BOARDS.txt') -Force
Copy-Item -LiteralPath $rangeProfilePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_PROFILE.json') -Force
Copy-Item -LiteralPath $oopRangePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_OOP.txt') -Force
Copy-Item -LiteralPath $ipRangePathAbs -Destination (Join-Path $outputDir 'INPUT_RANGE_IP.txt') -Force
Copy-Item -LiteralPath $oopRangePathAbs -Destination (Join-Path $outputDir ("INPUT_RANGE_{0}.txt" -f $OopPosition)) -Force
Copy-Item -LiteralPath $ipRangePathAbs -Destination (Join-Path $outputDir ("INPUT_RANGE_{0}.txt" -f $IpPosition)) -Force

$versionPath = Join-Path $root 'VERSION-v013.txt'
if (-not (Test-Path -LiteralPath $versionPath)) { $versionPath = Join-Path $root 'VERSION-v012.txt' }
if (Test-Path -LiteralPath $versionPath) {
    Copy-Item -LiteralPath $versionPath -Destination (Join-Path $outputDir 'RUNNER_VERSION.txt') -Force
}

$datasetSource = Join-Path $outputDir 'dataset.csv'
if (-not (Test-Path -LiteralPath $datasetSource -PathType Leaf)) {
    throw 'dataset.csv was not created.'
}

$datasetName = (($runName -replace '^OUT__', 'DS__') + '.csv')
$datasetPath = Join-Path $datasetsRoot $datasetName
Copy-Item -LiteralPath $datasetSource -Destination $datasetPath -Force

$inputs = [ordered]@{
    config = [ordered]@{ file = [IO.Path]::GetFileName($configPathAbs); sha256 = Get-Sha256 $configPathAbs }
    boards = [ordered]@{ file = [IO.Path]::GetFileName($boardsPathAbs); sha256 = Get-Sha256 $boardsPathAbs }
    range_profile = [ordered]@{ file = [IO.Path]::GetFileName($rangeProfilePathAbs); sha256 = Get-Sha256 $rangeProfilePathAbs }
    oop_range = [ordered]@{ position = $OopPosition; file = [IO.Path]::GetFileName($oopRangePathAbs); sha256 = Get-Sha256 $oopRangePathAbs }
    ip_range = [ordered]@{ position = $IpPosition; file = [IO.Path]::GetFileName($ipRangePathAbs); sha256 = Get-Sha256 $ipRangePathAbs }
}
if (-not $usingGenericRanges) {
    # Preserve the legacy manifest aliases for RNG001 consumers.
    $inputs['utg_range'] = [ordered]@{ file = [IO.Path]::GetFileName($ipRangePathAbs); sha256 = Get-Sha256 $ipRangePathAbs }
    $inputs['bb_range'] = [ordered]@{ file = [IO.Path]::GetFileName($oopRangePathAbs); sha256 = Get-Sha256 $oopRangePathAbs }
}

$manifest = [ordered]@{
    schema_version = 3
    run_id = $runName
    created_at = (Get-Date).ToString('o')
    resumed = $resuming
    range_id = $RangeId
    config_id = $ConfigId
    decision_id = $DecisionId
    decision_node = $DecisionNode
    oop_position = $OopPosition
    ip_position = $IpPosition
    board_set_id = $BoardSetId
    board_count = $boards.Count
    money_scale = $MoneyScale
    expected_bet_amount = $ExpectedBetAmount
    expected_raise_amount = $ExpectedRaiseAmount
    inputs = $inputs
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

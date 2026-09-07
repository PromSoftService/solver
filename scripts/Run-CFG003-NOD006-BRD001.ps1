[CmdletBinding()]
param(
    [string]$ResumeOutputDirectory = '',
    [switch]$ResumeLatestFailed
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'Range-Utils.ps1')

if ($ResumeOutputDirectory -and $ResumeLatestFailed) {
    throw 'Use either -ResumeOutputDirectory or -ResumeLatestFailed, not both.'
}

if ($ResumeLatestFailed) {
    $outputRoot = Join-Path $root 'output'
    $candidate = Get-ChildItem -LiteralPath $outputRoot -Directory -Filter 'OUT__RNG002__CFG003__NOD006__BRD001__RUN-*' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Where-Object {
            $summaryPath = Join-Path $_.FullName 'batch-summary.csv'
            if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) { return $false }
            return (@(Import-Csv -LiteralPath $summaryPath | Where-Object { $_.status -ne 'done' }).Count -gt 0)
        } |
        Select-Object -First 1
    if ($null -eq $candidate) {
        throw 'No incomplete RNG002/CFG003/NOD006/BRD001 output run was found.'
    }
    $ResumeOutputDirectory = $candidate.FullName
    Write-Host "Resuming latest incomplete run: $ResumeOutputDirectory"
}

$specRel = 'configs\CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.derived.json'
$specPath = Join-Path $root $specRel
$spec = Get-Content -LiteralPath $specPath -Raw -Encoding UTF8 | ConvertFrom-Json
$baseConfigPath = Join-Path $root ([string]$spec.base_config)

$rangeProfileRel = 'ranges\RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1.json'
$utgRangeRel = 'ranges\RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1__UTG.txt'
$btnRangeRel = 'ranges\RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1__BTN.txt'
$utgRangePath = Join-Path $root $utgRangeRel
$btnRangePath = Join-Path $root $btnRangeRel

$effectiveConfigName = 'CFG003__6M100_UTG-O2p5_BTN-C__F_OOP-B33-XR60_IP-B33-R100__T-B100-R100__R-B100-R100__V1.json'
$tempDir = Join-Path ([IO.Path]::GetTempPath()) ('tsgpu-cfg003-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($tempDir) | Out-Null
$effectiveConfigPath = Join-Path $tempDir $effectiveConfigName

try {
    $config = Get-Content -LiteralPath $baseConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (@($config.config.ipRange).Count -ne 1326) { throw 'CFG001 ipRange is not 1326 entries.' }
    if (@($config.config.oopRange).Count -ne 1326) { throw 'CFG001 oopRange is not 1326 entries.' }
    if ([int]$config.config.effectiveStack -ne 975) { throw 'CFG001 effectiveStack changed; CFG003 derivation must be reviewed.' }

    $config.config.oopRange = @(Convert-TexasSolverRangeTo1326 -Path $utgRangePath)
    $config.config.ipRange = @(Convert-TexasSolverRangeTo1326 -Path $btnRangePath)
    $config.config.startingPot = [int]$spec.overrides.startingPot
    $config.config.effectiveStack = [int]$spec.overrides.effectiveStack
    $config.config.oopFlopBet = [string]$spec.overrides.oopFlopBet
    $config.config.oopFlopRaise = [string]$spec.overrides.oopFlopRaise
    $config.config.ipFlopBet = [string]$spec.overrides.ipFlopBet
    $config.config.ipFlopRaise = [string]$spec.overrides.ipFlopRaise
    $config | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $effectiveConfigPath -Encoding UTF8

    $utgCombos = Get-TexasSolverWeightedComboCount -Path $utgRangePath
    $btnCombos = Get-TexasSolverWeightedComboCount -Path $btnRangePath
    Write-Host ("RNG002: UTG {0:N3} weighted combos; BTN {1:N3} weighted combos" -f $utgCombos, $btnCombos)
    Write-Host "CFG003: flop pot 6.5bb, UTG OOP Check/Bet 33%, BTN after check Check/Bet 33%"
    Write-Host "NOD006: export UTG response after UTG check -> BTN B33; expected native Bet $($spec.expected_native_actions.btn_stab_bet), Raise $($spec.expected_native_actions.utg_response_raise)"
    Write-Host ''

    $studyArgs = @{
        RangeId = 'RNG002'
        ConfigId = 'CFG003'
        DecisionId = 'NOD006'
        DecisionNode = 'UTG_RESPONSE'
        BoardSetId = 'BRD001'
        ConfigPath = $effectiveConfigPath
        BoardsPath = 'boards\BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt'
        RangeProfilePath = $rangeProfileRel
        OopRangePath = $utgRangeRel
        IpRangePath = $btnRangeRel
        OopPosition = 'UTG'
        IpPosition = 'BTN'
        ExpectedBetAmount = [int]$spec.expected_native_actions.btn_stab_bet
        ExpectedRaiseAmount = [int]$spec.expected_native_actions.utg_response_raise
        MoneyScale = [double]$spec.money_scale
    }
    if ($ResumeOutputDirectory) {
        $studyArgs['ResumeOutputDirectory'] = $ResumeOutputDirectory
    }

    & (Join-Path $PSScriptRoot 'Run-Study.ps1') @studyArgs
}
finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

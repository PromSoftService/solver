[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$specPath = Join-Path $root 'configs\CFG002__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B75_BB-XR60__T-B100-R100__R-B100-R100__V1.derived.json'
$spec = Get-Content -LiteralPath $specPath -Raw -Encoding UTF8 | ConvertFrom-Json
$baseConfigPath = Join-Path $root ([string]$spec.base_config)

$effectiveConfigName = 'CFG002__6M100_UTG-O2p5_BB-C__F_BB-X_UTG-B75_BB-XR60__T-B100-R100__R-B100-R100__V1.json'
$tempDir = Join-Path ([IO.Path]::GetTempPath()) ('tsgpu-cfg002-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($tempDir) | Out-Null
$effectiveConfigPath = Join-Path $tempDir $effectiveConfigName

try {
    $config = Get-Content -LiteralPath $baseConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

    if (@($config.config.ipRange).Count -ne 1326) { throw 'CFG001 ipRange is not 1326 entries.' }
    if (@($config.config.oopRange).Count -ne 1326) { throw 'CFG001 oopRange is not 1326 entries.' }
    if ([int]$config.config.startingPot -ne 55) { throw 'CFG001 startingPot changed; CFG002 derivation is no longer valid.' }
    if ([int]$config.config.effectiveStack -ne 975) { throw 'CFG001 effectiveStack changed; CFG002 derivation is no longer valid.' }
    if ([string]$config.config.oopFlopRaise -ne '60') { throw 'CFG001 oopFlopRaise changed; CFG002 derivation is no longer valid.' }

    $config.config.ipFlopBet = [string]$spec.overrides.ipFlopBet
    $config | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $effectiveConfigPath -Encoding UTF8

    Write-Host "CFG002: materialized from CFG001 with UTG flop bet $($spec.overrides.ipFlopBet)%"
    Write-Host "Expected native node: Check -> Bet $($spec.expected_native_actions.bet) -> Fold/Call/Raise $($spec.expected_native_actions.raise)"
    Write-Host ''

    & (Join-Path $PSScriptRoot 'Run-Study.ps1') `
        -RangeId 'RNG001' `
        -ConfigId 'CFG002' `
        -BoardSetId 'BRD001' `
        -ConfigPath $effectiveConfigPath `
        -BoardsPath 'boards\BRD001__FLOP_UNPAIRED_RAINBOW__ISO286__V1.txt' `
        -RangeProfilePath 'ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1.json' `
        -UtgRangePath 'ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__UTG.txt' `
        -BbRangePath 'ranges\RNG001__TSGPU020_6M100_UTG-O2p5_BB-C__V1__BB.txt' `
        -ExpectedBetAmount ([int]$spec.expected_native_actions.bet) `
        -ExpectedRaiseAmount ([int]$spec.expected_native_actions.raise) `
        -MoneyScale 10
}
finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

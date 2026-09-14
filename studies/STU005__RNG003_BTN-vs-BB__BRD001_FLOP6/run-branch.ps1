[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('01_BB_FIRST', '02_BTN_AFTER_CHECK', '03_BB_AFTER_CBET', '04_BTN_AFTER_CHECK_RAISE', '05_BTN_AFTER_DONK', '06_BB_AFTER_DONK_RAISE')]
    [string]$BranchId,
    [string]$OutputDirectory = '',
    [string]$DatasetDirectory = '',
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$launcher = Join-Path $repoRoot 'scripts\run-flop-study-branch.ps1'
& $launcher @PSBoundParameters -StudyDirectory $PSScriptRoot

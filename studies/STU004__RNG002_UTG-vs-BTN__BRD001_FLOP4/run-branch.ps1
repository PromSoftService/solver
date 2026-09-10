[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('01_UTG_FIRST', '02_BTN_AFTER_CHECK', '03_BTN_AFTER_CBET', '04_UTG_AFTER_STAB')]
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

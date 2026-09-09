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
$pilotLauncher = Join-Path $PSScriptRoot '..\STU003__RNG002_UTG-vs-BTN__5FLOP_FLOP4\run-branch.ps1'
& $pilotLauncher @PSBoundParameters -StudyDirectory $PSScriptRoot

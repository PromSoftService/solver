[CmdletBinding()]
param(
    [string]$OutputRoot = '',
    [string]$DatasetRoot = '',
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$pilotLauncher = Join-Path $PSScriptRoot '..\STU003__RNG002_UTG-vs-BTN__5FLOP_FLOP4\run-all.ps1'
& $pilotLauncher @PSBoundParameters -StudyDirectory $PSScriptRoot

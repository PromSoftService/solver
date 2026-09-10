[CmdletBinding()]
param(
    [string]$OutputRoot = '',
    [string]$DatasetRoot = '',
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$launcher = Join-Path $repoRoot 'scripts\run-flop-study-all.ps1'
& $launcher @PSBoundParameters -StudyDirectory $PSScriptRoot

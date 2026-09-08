[CmdletBinding()]
param(
    [string]$SolverExe = '',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$branchIds = @(
    '01_BB_FIRST',
    '02_UTG_AFTER_CHECK',
    '03_BB_AFTER_CBET',
    '04_UTG_AFTER_CHECK_RAISE',
    '05_UTG_AFTER_DONK',
    '06_BB_AFTER_DONK_RAISE'
)

foreach ($branchId in $branchIds) {
    $arguments = @{
        BranchId = $branchId
        Resume = $Resume
    }
    if ($SolverExe) { $arguments['SolverExe'] = $SolverExe }
    & (Join-Path $PSScriptRoot 'run-branch.ps1') @arguments
}

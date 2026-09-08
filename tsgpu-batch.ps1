[CmdletBinding()]
param(
    [Parameter(Mandatory=$true,Position=0)][string]$Config,
    [Parameter(Mandatory=$true,Position=1)][string]$Boards,
    [Parameter(Mandatory=$true,Position=2)][string]$OutputDirectory,
    [string]$SolverExe = '',
    [Nullable[int]]$MaxIterations = $null,
    [Nullable[double]]$TargetExploitability = $null,
    [int]$ExportMaxNodes = 2000000,
    [int]$SolveTimeoutMinutes = 240,
    [switch]$Resume,
    [switch]$ShowHostWindow
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$configPath = (Resolve-Path -LiteralPath $Config).Path
$boardsPath = (Resolve-Path -LiteralPath $Boards).Path
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($outputPath) | Out-Null
if (-not $SolverExe) {
    $solverCandidates = @(
        $env:TSGPU_SOLVER_EXE,
        (Join-Path $PSScriptRoot '..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),
        (Join-Path $PSScriptRoot 'TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),
        (Join-Path $PSScriptRoot '..\TexasSolverGpu_131.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
    $SolverExe = $solverCandidates | Select-Object -First 1
}
if (-not $SolverExe) { throw 'TexasSolverGpu_131.exe not found. Set TSGPU_SOLVER_EXE or keep solver directory next to repo.' }
$solverPath = (Resolve-Path -LiteralPath $SolverExe).Path
$doc = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
function Read-Setting([string]$Name,[object]$Default) {
    foreach ($containerName in @('runner','solve')) {
        $container = $doc.PSObject.Properties[$containerName]
        if ($null -ne $container) {
            $value = $container.Value.PSObject.Properties[$Name]
            if ($null -ne $value) { return $value.Value }
        }
    }
    return $Default
}
$effectiveIterations = if ($null -ne $MaxIterations) { [int]$MaxIterations } else { [int](Read-Setting 'maxIterations' 1000) }
$effectiveTarget = if ($null -ne $TargetExploitability) { [double]$TargetExploitability } else { [double](Read-Setting 'targetExploitability' 0.5) }
$boardList = @(Get-Content -LiteralPath $boardsPath -Encoding UTF8 | ForEach-Object { $line=$_.Trim(); if ($line -and -not $line.StartsWith('#')) { $line } })
if ($boardList.Count -eq 0) { throw 'No boards found.' }
$summary = [Collections.Generic.List[object]]::new()
$failed = 0
for ($i=0; $i -lt $boardList.Count; $i++) {
    $board = $boardList[$i]
    $index = $i + 1
    $slug = ($board -replace '[^0-9A-Za-z]+','_').Trim('_')
    $jobName = ('{0:D4}_{1}' -f $index,$slug)
    $jobOutput = Join-Path $outputPath $jobName
    $runPath = Join-Path $jobOutput 'run.json'
    $metaPath = Join-Path $jobOutput 'tree.meta.json'
    if ($Resume -and (Test-Path $runPath) -and (Test-Path $metaPath)) {
        try {
            $meta = Get-Content $metaPath -Raw | ConvertFrom-Json
            if ($meta.full_tree_validated) {
                $run = Get-Content $runPath -Raw | ConvertFrom-Json
                Write-Host "[$index/$($boardList.Count)] $board (already done)"
                $summary.Add([pscustomobject]@{index=$index;board=$board;status='done';iteration=$run.final_status.iteration;exploitability=$run.final_status.exploitability;elapsed_ms=$run.elapsed_ms;error=''})
                continue
            }
        } catch {}
    }
    if (Test-Path $jobOutput) { Remove-Item $jobOutput -Recurse -Force }
    Write-Host "[$index/$($boardList.Count)] $board"
    try {
        & (Join-Path $PSScriptRoot 'tsgpu-worker.ps1') -SolverExe $solverPath -Config $configPath -Board $board -OutputDirectory $jobOutput -MaxIterations $effectiveIterations -TargetExploitability $effectiveTarget -ExportMaxNodes $ExportMaxNodes -SolveTimeoutMinutes $SolveTimeoutMinutes -ShowHostWindow:$ShowHostWindow
        if (-not (Test-Path $runPath) -or -not (Test-Path $metaPath)) { throw 'Full-tree artifacts missing.' }
        $run = Get-Content $runPath -Raw | ConvertFrom-Json
        $meta = Get-Content $metaPath -Raw | ConvertFrom-Json
        if (-not $meta.full_tree_validated) { throw 'Full-tree validation is false.' }
        $summary.Add([pscustomobject]@{index=$index;board=$board;status='done';iteration=$run.final_status.iteration;exploitability=$run.final_status.exploitability;elapsed_ms=$run.elapsed_ms;error=''})
    } catch {
        $failed++
        $summary.Add([pscustomobject]@{index=$index;board=$board;status='error';iteration=0;exploitability=$null;elapsed_ms=0;error=$_.Exception.Message})
        Write-Error -ErrorAction Continue "Board $board failed: $($_.Exception.Message)"
    }
}
$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $outputPath 'batch-summary.json') -Encoding UTF8
$summary | Export-Csv -LiteralPath (Join-Path $outputPath 'batch-summary.csv') -NoTypeInformation -Encoding UTF8
Write-Host "Batch complete: $($boardList.Count-$failed) done, $failed failed."
if ($failed -gt 0) { throw "$failed board(s) failed; study MUST NOT be committed or pushed." }

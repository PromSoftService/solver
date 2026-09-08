[CmdletBinding()]
param(
  [Parameter(Mandatory=$true,Position=0)][string]$Config,
  [Parameter(Mandatory=$true,Position=1)][string]$Boards,
  [Parameter(Mandatory=$true,Position=2)][string]$OutputDirectory,
  [string]$SolverExe='',
  [Nullable[int]]$MaxIterations=$null,
  [Nullable[double]]$TargetExploitability=$null,
  [int]$ExportMaxNodes=2000000,
  [int]$SolveTimeoutMinutes=240,
  [switch]$Resume,
  [switch]$ShowHostWindow
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$configPath=(Resolve-Path -LiteralPath $Config).Path;$boardsPath=(Resolve-Path -LiteralPath $Boards).Path;$outputPath=[IO.Path]::GetFullPath($OutputDirectory);[IO.Directory]::CreateDirectory($outputPath)|Out-Null
if(-not$SolverExe){$candidates=@($env:TSGPU_SOLVER_EXE,(Join-Path$PSScriptRoot'..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),(Join-Path$PSScriptRoot'TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'),(Join-Path$PSScriptRoot'..\TexasSolverGpu_131.exe'))|?{$_-and(Test-Path -LiteralPath $_ -PathType Leaf)};$SolverExe=$candidates|select -First 1};if(-not$SolverExe){throw 'TexasSolverGpu_131.exe not found. Set TSGPU_SOLVER_EXE or place solver directory next to repo.'};$solverPath=(Resolve-Path -LiteralPath $SolverExe).Path
$doc=Get-Content -LiteralPath$configPath -Raw -Encoding UTF8|ConvertFrom-Json;function Setting([string]$n,[object]$d){foreach($container in@('runner','solve')){$p=$doc.PSObject.Properties[$container];if($null-ne$p){$q=$p.Value.PSObject.Properties[$n];if($null-ne$q){return$q.Value}}};return$d};$iters=if($null-ne$MaxIterations){[int]$MaxIterations}else{[int](Setting'maxIterations'1000)};$target=if($null-ne$TargetExploitability){[double]$TargetExploitability}else{[double](Setting'targetExploitability'0.5)}
$boardList=@(Get-Content -LiteralPath$boardsPath -Encoding UTF8|%{$x=$_.Trim();if($x-and-not$x.StartsWith('#')){$x}});if($boardList.Count-eq0){throw 'No boards found'}
$summary=[Collections.Generic.List[object]]::new();$failed=0
for($i=0;$i-lt$boardList.Count;$i++){$board=$boardList[$i];$idx=$i+1;$slug=($board-replace'[^0-9A-Za-z]+','_').Trim('_');$dir=Join-Path$outputPath('{0:D4}_{1}'-f$idx,$slug);$runPath=Join-Path$dir'run.json';$metaPath=Join-Path$dir'tree.meta.json';if($Resume-and(Test-Path$runPath)-and(Test-Path$metaPath)){try{$m=Get-Content$metaPath -Raw|ConvertFrom-Json;if($m.full_tree_validated){Write-Host "[$idx/$($boardList.Count)] $board (already done)";$r=Get-Content$runPath -Raw|ConvertFrom-Json;$summary.Add([pscustomobject]@{index=$idx;board=$board;status='done';iteration=$r.final_status.iteration;exploitability=$r.final_status.exploitability;elapsed_ms=$r.elapsed_ms;error=''});continue}}catch{}};if(Test-Path$dir){Remove-Item$dir -Recurse -Force};Write-Host "[$idx/$($boardList.Count)] $board";try{& (Join-Path$PSScriptRoot'tsgpu-worker.ps1') -SolverExe$solverPath -Config$configPath -Board$board -OutputDirectory$dir -MaxIterations$iters -TargetExploitability$target -ExportMaxNodes$ExportMaxNodes -SolveTimeoutMinutes$SolveTimeoutMinutes -ShowHostWindow:$ShowHostWindow;if(-not(Test-Path$runPath)-or-not(Test-Path$metaPath)){throw 'Full-tree artifacts missing'};$r=Get-Content$runPath -Raw|ConvertFrom-Json;$m=Get-Content$metaPath -Raw|ConvertFrom-Json;if(-not$m.full_tree_validated){throw 'Full-tree validation false'};$summary.Add([pscustomobject]@{index=$idx;board=$board;status='done';iteration=$r.final_status.iteration;exploitability=$r.final_status.exploitability;elapsed_ms=$r.elapsed_ms;error=''})}catch{$failed++;$summary.Add([pscustomobject]@{index=$idx;board=$board;status='error';iteration=0;exploitability=$null;elapsed_ms=0;error=$_.Exception.Message});Write-Error -ErrorAction Continue "Board $board failed: $($_.Exception.Message)"}}
$summary|ConvertTo-Json -Depth 10|Set-Content -LiteralPath(Join-Path$outputPath'batch-summary.json') -Encoding UTF8;$summary|Export-Csv -LiteralPath(Join-Path$outputPath'batch-summary.csv') -NoTypeInformation -Encoding UTF8
Write-Host "Batch complete: $($boardList.Count-$failed) done, $failed failed.";if($failed-gt0){throw "$failed board(s) failed; study MUST NOT be committed or pushed."}

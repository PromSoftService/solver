[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SolverExe,
    [Parameter(Mandatory=$true)][string]$Config,
    [Parameter(Mandatory=$true)][string]$Board,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [int]$MaxIterations = 1000,
    [double]$TargetExploitability = 0.5,
    [int]$ExportMaxNodes = 2000000,
    [int]$SolveTimeoutMinutes = 240,
    [switch]$ShowHostWindow
)

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ScriptVersion='v020-fulltree'
$StatusRetryLimit=5

if (-not ('TsGpu.WindowHider' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Threading;
namespace TsGpu {
  public static class WindowHider {
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lp);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] static extern bool ShowWindowAsync(IntPtr hWnd, int cmd);
    static volatile bool running; static int targetPid; static Thread thread;
    static bool One(IntPtr hWnd, IntPtr lp) { uint p; GetWindowThreadProcessId(hWnd,out p); if (p==(uint)targetPid) ShowWindowAsync(hWnd,0); return true; }
    static void Pump(){ EnumWindowsProc cb=One; while(running){ EnumWindows(cb,IntPtr.Zero); Thread.Sleep(25); } }
    public static void Start(int pid){ Stop(); targetPid=pid; running=true; thread=new Thread(Pump); thread.IsBackground=true; thread.Start(); }
    public static void Stop(){ running=false; if(thread!=null && thread.IsAlive) thread.Join(1000); thread=null; targetPid=0; }
  }
}
'@
}

function ConvertTo-CompactJson([object]$Value,[int]$Depth=100){ ConvertTo-Json -InputObject $Value -Depth $Depth -Compress }
function Read-Property([object]$Object,[string]$Name,[object]$Default=$null){ if($null-eq $Object){return $Default}; $p=$Object.PSObject.Properties[$Name]; if($null-eq $p){return $Default}; return $p.Value }
function Get-FreeTcpPort { $l=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0); $l.Start(); try{return ([Net.IPEndPoint]$l.LocalEndpoint).Port} finally{$l.Stop()} }
function Convert-CardToId([string]$Card){ if($Card -notmatch '^[2-9TJQKA][cdhs]$'){throw "Invalid card: $Card"}; $r='23456789TJQKA'.IndexOf($Card.Substring(0,1).ToUpperInvariant()); $s='cdhs'.IndexOf($Card.Substring(1,1).ToLowerInvariant()); return $r*4+$s }
function Convert-Board([string]$Text){ $t=@($Text -split '[\s,]+'|?{$_}); if($t.Count-ne3){throw 'Each board must contain exactly three flop cards.'}; $ids=@($t|%{Convert-CardToId $_}); if(@($ids|select -Unique).Count-ne3){throw 'Duplicate board card.'}; return $ids }
function Convert-Sizing([object]$Value){ if($null-eq $Value){return ''}; $items=@(([string]$Value).Replace(';',',') -split '[\s,|/]+'|%{$v=$_.Trim().ToLowerInvariant(); if($v){if($v-match'^\d+(\.\d+)?$'){"$v%"}else{$v}}}); return $items-join',' }

function Convert-ToNativeConfig([object]$InputConfig,[int[]]$BoardIds){
  $c=Read-Property $InputConfig 'config' $InputConfig; $oop=@(Read-Property $c 'oopRange' @()); $ip=@(Read-Property $c 'ipRange' @());
  if($oop.Count-ne1326 -or $ip.Count-ne1326){throw "Both ranges must contain 1326 combo weights."}
  [ordered]@{
    oop_range=$oop; ip_range=$ip; board=$BoardIds;
    starting_pot=[double](Read-Property $c 'startingPot' 0); effective_stack=[double](Read-Property $c 'effectiveStack' 0);
    rake_rate=[double](Read-Property $c 'rakeRate' 0); rake_cap=[double](Read-Property $c 'rakeCap' 0);
    oop_flop_bet=Convert-Sizing(Read-Property $c 'oopFlopBet' ''); oop_flop_raise=Convert-Sizing(Read-Property $c 'oopFlopRaise' '');
    ip_flop_bet=Convert-Sizing(Read-Property $c 'ipFlopBet' ''); ip_flop_raise=Convert-Sizing(Read-Property $c 'ipFlopRaise' '');
    oop_turn_bet=Convert-Sizing(Read-Property $c 'oopTurnBet' ''); oop_turn_raise=Convert-Sizing(Read-Property $c 'oopTurnRaise' '');
    ip_turn_bet=Convert-Sizing(Read-Property $c 'ipTurnBet' ''); ip_turn_raise=Convert-Sizing(Read-Property $c 'ipTurnRaise' '');
    oop_river_bet=Convert-Sizing(Read-Property $c 'oopRiverBet' ''); oop_river_raise=Convert-Sizing(Read-Property $c 'oopRiverRaise' '');
    ip_river_bet=Convert-Sizing(Read-Property $c 'ipRiverBet' ''); ip_river_raise=Convert-Sizing(Read-Property $c 'ipRiverRaise' '');
    donk_option=$true; oop_turn_donk=Convert-Sizing(Read-Property $c 'oopTurnDonk' ''); oop_river_donk=Convert-Sizing(Read-Property $c 'oopRiverDonk' '');
    max_raise_number=[Math]::Max(0,[Math]::Min(255,[int](Read-Property $c 'maxRaiseNumber' 1)));
    add_allin_threshold=[Math]::Max(0,[double](Read-Property $c 'addAllinThreshold' 2000)/100.0); force_allin_threshold=0.2;
    add_allin_flop_ip=[bool](Read-Property $c 'addAllinFlopIp' $true); add_allin_turn_ip=[bool](Read-Property $c 'addAllinTurnIp' $true); add_allin_river_ip=[bool](Read-Property $c 'addAllinRiverIp' $true);
    add_allin_flop_oop=[bool](Read-Property $c 'addAllinFlopOop' $true); add_allin_turn_oop=[bool](Read-Property $c 'addAllinTurnOop' $true); add_allin_river_oop=[bool](Read-Property $c 'addAllinRiverOop' $true);
    merging_threshold=0.1; num_players=2
  }
}

function Wait-Task([Threading.Tasks.Task]$Task,[int]$TimeoutMs,[string]$What){ if(-not $Task.Wait($TimeoutMs)){throw "Timeout waiting for $What"}; if($Task.IsFaulted){throw $Task.Exception.GetBaseException()}; $Task }
function Receive-WebSocketText([Net.WebSockets.ClientWebSocket]$Socket,[int]$TimeoutMs){ $ms=[IO.MemoryStream]::new(); try{do{$b=New-Object byte[] 65536;$seg=[ArraySegment[byte]]::new($b);$cts=[Threading.CancellationTokenSource]::new($TimeoutMs);try{$task=$Socket.ReceiveAsync($seg,$cts.Token);Wait-Task $task $TimeoutMs 'DevTools response'|Out-Null;$r=$task.Result}finally{$cts.Dispose()};if($r.MessageType-eq[Net.WebSockets.WebSocketMessageType]::Close){throw 'DevTools socket closed'};$ms.Write($b,0,$r.Count)}while(-not $r.EndOfMessage);[Text.Encoding]::UTF8.GetString($ms.ToArray())}finally{$ms.Dispose()} }
$script:CdpId=0
function Invoke-Cdp([Net.WebSockets.ClientWebSocket]$Socket,[string]$Method,[object]$Params,[int]$TimeoutMs=120000){$script:CdpId++;$id=$script:CdpId;$req=ConvertTo-CompactJson([ordered]@{id=$id;method=$Method;params=$Params});$bytes=[Text.Encoding]::UTF8.GetBytes($req);$send=$Socket.SendAsync([ArraySegment[byte]]::new($bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None);Wait-Task $send $TimeoutMs 'DevTools send'|Out-Null;while($true){$m=Receive-WebSocketText $Socket $TimeoutMs|ConvertFrom-Json;$mid=Read-Property $m 'id' $null;if($null-ne$mid-and[int]$mid-eq$id){$err=Read-Property $m 'error' $null;if($null-ne$err){throw "CDP $Method failed: $(ConvertTo-CompactJson $err)"};return Read-Property $m 'result' $null}}}
function Invoke-JavaScript([Net.WebSockets.ClientWebSocket]$Socket,[string]$Expression,[int]$TimeoutMs=120000){$r=Invoke-Cdp $Socket 'Runtime.evaluate' ([ordered]@{expression=$Expression;awaitPromise=$true;returnByValue=$true;userGesture=$true}) $TimeoutMs;$ex=Read-Property $r 'exceptionDetails' $null;if($null-ne$ex){throw "JavaScript failed: $(ConvertTo-CompactJson $ex)"};return Read-Property(Read-Property $r 'result' $null)'value' $null}
function New-BridgeBootstrap{return @'
(()=>{if(window.__tsgpuPoc)return true;if(!window.chrome||!window.chrome.webview)throw new Error('Native WebView2 bridge unavailable');const s={seq:1,pending:new Map(),token:null};window.chrome.webview.addEventListener('message',e=>{let m=e.data;if(typeof m==='string'){try{m=JSON.parse(m)}catch(_){return}}if(!m||typeof m.id!=='string')return;const p=s.pending.get(m.id);if(!p)return;clearTimeout(p.timer);s.pending.delete(m.id);p.resolve(m)});s.call=(method,params,timeoutMs)=>new Promise((resolve,reject)=>{const id=`poc_${Date.now()}_${s.seq++}`;const timer=setTimeout(()=>{s.pending.delete(id);reject(new Error(`Bridge timeout: ${method}`))},timeoutMs);s.pending.set(id,{resolve,reject,timer});window.chrome.webview.postMessage(JSON.stringify({id,method,params}))});s.request=async(method,path,httpMethod,body,timeoutMs)=>{if(s.token===null){const p=await s.call('bridge.ping',{},3000);if(!p.ok)throw new Error(`bridge.ping: ${JSON.stringify(p.error)}`);s.token=p.result&&typeof p.result.bridge_token==='string'?p.result.bridge_token:''}const params={apiBase:'http://127.0.0.1:6006',path,method:httpMethod,bridge_token:s.token};if(body!==null&&body!==undefined)params.body=body;let r=await s.call(method,params,timeoutMs);if(!r.ok&&r.error&&r.error.code==='UNAUTHORIZED'){s.token=null;return s.request(method,path,httpMethod,body,timeoutMs)}if(!r.ok)throw new Error(`${method}: ${JSON.stringify(r.error)}`);return r.result};s.requestObject=q=>s.request(q.nativeMethod,q.path,q.httpMethod,Object.prototype.hasOwnProperty.call(q,'body')?q.body:undefined,Number(q.timeoutMs));window.__tsgpuPoc=s;return true})()
'@}
function Invoke-Bridge([Net.WebSockets.ClientWebSocket]$Socket,[string]$NativeMethod,[string]$Path,[string]$HttpMethod,[object]$Body,[int]$TimeoutMs,[Collections.Generic.List[object]]$Transcript){$q=[ordered]@{nativeMethod=$NativeMethod;path=$Path;httpMethod=$HttpMethod;timeoutMs=$TimeoutMs};if($null-ne$Body){$q.body=$Body};$started=[DateTime]::UtcNow;try{$r=Invoke-JavaScript $Socket "window.__tsgpuPoc.requestObject($(ConvertTo-CompactJson $q))" ($TimeoutMs+5000);$Transcript.Add([ordered]@{at=$started.ToString('o');method=$NativeMethod;path=$Path;elapsed_ms=[int]([DateTime]::UtcNow-$started).TotalMilliseconds;result='ok'});return $r}catch{$Transcript.Add([ordered]@{at=$started.ToString('o');method=$NativeMethod;path=$Path;elapsed_ms=[int]([DateTime]::UtcNow-$started).TotalMilliseconds;error=$_.Exception.Message});throw}}

function Test-FullTreeText([string]$Json){
  $hasChildren=$Json -match '"childrens"'; $hasStrategy=$Json -match '"strategy"';
  $hasTurn=($Json -match '"betting round"\s*:\s*2') -or ($Json -match '"betting_round"\s*:\s*2');
  $hasRiver=($Json -match '"betting round"\s*:\s*3') -or ($Json -match '"betting_round"\s*:\s*3');
  [pscustomobject]@{valid=($hasChildren-and$hasStrategy-and$hasTurn-and$hasRiver);has_children=$hasChildren;has_strategy=$hasStrategy;has_turn=$hasTurn;has_river=$hasRiver}
}
function Write-GzipText([string]$Text,[string]$Path){$fs=[IO.File]::Open($Path,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$gz=[IO.Compression.GZipStream]::new($fs,[IO.Compression.CompressionLevel]::Optimal,$false);try{$sw=[IO.StreamWriter]::new($gz,[Text.UTF8Encoding]::new($false));try{$sw.Write($Text)}finally{$sw.Dispose()}}finally{$gz.Dispose()}}finally{$fs.Dispose()}}
function Split-GitSafe([string]$Path,[int64]$MaxBytes=90000000){$f=Get-Item -LiteralPath $Path;if($f.Length-le$MaxBytes){return @([IO.Path]::GetFileName($Path))};$parts=[Collections.Generic.List[string]]::new();$src=[IO.File]::OpenRead($Path);try{$idx=1;while($src.Position-lt$src.Length){$name=([IO.Path]::GetFileName($Path)+('.part{0:D3}'-f$idx));$dstPath=Join-Path([IO.Path]::GetDirectoryName($Path))$name;$dst=[IO.File]::Create($dstPath);try{$remaining=[Math]::Min($MaxBytes,$src.Length-$src.Position);$buf=New-Object byte[] 1048576;while($remaining-gt0){$n=$src.Read($buf,0,[int][Math]::Min($buf.Length,$remaining));if($n-le0){break};$dst.Write($buf,0,$n);$remaining-=$n}}finally{$dst.Dispose()};$parts.Add($name);$idx++}}finally{$src.Dispose()};Remove-Item -LiteralPath $Path -Force;return $parts.ToArray()}
function Get-FrontendExportHints([Net.WebSockets.ClientWebSocket]$Socket){$js=@'
(async()=>{const hits=[];for(const s of [...document.scripts]){if(!s.src)continue;try{const t=await (await fetch(s.src)).text();for(const re of [/solver\.[A-Za-z0-9_.]*(?:export|dump)[A-Za-z0-9_.]*/g,/\/api\/[A-Za-z0-9_./-]*(?:export|dump)[A-Za-z0-9_./-]*/g]){for(const m of (t.match(re)||[]))hits.push(m)}}catch(_){}}return [...new Set(hits)].slice(0,300)})()
'@;try{return @(Invoke-JavaScript $Socket $js 30000)}catch{return @("hint probe failed: $($_.Exception.Message)")}}

$solverPath=(Resolve-Path -LiteralPath $SolverExe).Path;$configPath=(Resolve-Path -LiteralPath $Config).Path;$outputPath=[IO.Path]::GetFullPath($OutputDirectory);[IO.Directory]::CreateDirectory($outputPath)|Out-Null
$boardIds=@(Convert-Board $Board);$inputConfig=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8|ConvertFrom-Json;$nativeConfig=Convert-ToNativeConfig $inputConfig $boardIds
$transcript=[Collections.Generic.List[object]]::new();$port=Get-FreeTcpPort;$process=$null;$socket=$null;$runStarted=[DateTime]::UtcNow
try{
  $start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=$solverPath;$start.WorkingDirectory=[IO.Path]::GetDirectoryName($solverPath);$start.UseShellExecute=$false;$start.CreateNoWindow=-not$ShowHostWindow;$start.WindowStyle=if($ShowHostWindow){[Diagnostics.ProcessWindowStyle]::Normal}else{[Diagnostics.ProcessWindowStyle]::Hidden};$start.EnvironmentVariables['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']="--remote-debugging-port=$port --remote-allow-origins=http://127.0.0.1:$port";$process=[Diagnostics.Process]::Start($start);if($null-eq$process){throw 'Failed to launch solver'};if(-not$ShowHostWindow){[TsGpu.WindowHider]::Start($process.Id)}
  $deadline=[DateTime]::UtcNow.AddSeconds(45);$target=$null;$http=[Net.WebClient]::new();try{while([DateTime]::UtcNow-lt$deadline-and$null-eq$target){if($process.HasExited){throw "Solver exited during startup: $($process.ExitCode)"};try{$targets=@($http.DownloadString("http://127.0.0.1:$port/json/list")|ConvertFrom-Json);$target=$targets|?{$_.type-eq'page'-and($_.url-like'https://appassets.local/*'-or$_.url-like'*index.html*')}|select -First 1;if($null-eq$target){$target=$targets|?{$_.type-eq'page'}|select -First 1}}catch{Start-Sleep -Milliseconds 250}}}finally{$http.Dispose()};if($null-eq$target){throw 'WebView2 DevTools application page not found'}
  $socket=[Net.WebSockets.ClientWebSocket]::new();$socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()|Out-Null;Invoke-Cdp $socket 'Runtime.enable' @{} 10000|Out-Null;Invoke-JavaScript $socket (New-BridgeBootstrap) 10000|Out-Null
  Invoke-Bridge $socket 'solver.init' '/api/init' 'POST' $nativeConfig 120000 $transcript|Out-Null;Invoke-Bridge $socket 'solver.allocate' '/api/allocate' 'POST' ([ordered]@{enable_compression=$false}) 120000 $transcript|Out-Null;$pre=Invoke-Bridge $socket 'solver.solve.status' '/api/solve/status' 'GET' $null 5000 $transcript
  $solveBody=[ordered]@{max_iterations=[Math]::Max(1,$MaxIterations);target_exploitability=[Math]::Max([double]0,[double]$TargetExploitability);compute_initial_exploitability=$true;verbose=$false};Invoke-Bridge $socket 'solver.solve.start' '/api/gpu-solve' 'POST' $solveBody 30000 $transcript|Out-Null
  $solveDeadline=[DateTime]::UtcNow.AddMinutes($SolveTimeoutMinutes);$status=$null;$timeouts=0;$seen=$false;do{Start-Sleep -Milliseconds 500;try{$status=Invoke-Bridge $socket 'solver.solve.status' '/api/solve/status' 'GET' $null 5000 $transcript;$timeouts=0}catch{if($_.Exception.Message-like'*Bridge timeout*'){$timeouts++;if($timeouts-ge$StatusRetryLimit){throw};continue}else{throw}};$running=[bool](Read-Property $status 'running' $false);if($running){$seen=$true};$phase=([string](Read-Property $status 'phase' '')).ToLowerInvariant();if($phase-eq'error'-or(Read-Property $status 'last_error' '')){throw "Native solve failed: $(Read-Property $status 'last_error' '')"};if([DateTime]::UtcNow-ge$solveDeadline){throw "Solve exceeded $SolveTimeoutMinutes minutes"};$terminal=$phase-in@('done','finished','completed','solved')}while($running-or(-not$seen-and-not$terminal))
  Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{history=@()}) 10000 $transcript|Out-Null
  $body=[ordered]@{history=@();max_nodes=$ExportMaxNodes;dump_rounds=2};$candidates=@(
    [ordered]@{method='solver.export.currentStreet';path='/api/export/current-street'},
    [ordered]@{method='solver.export.fullTree';path='/api/export/full-tree'},
    [ordered]@{method='solver.export.fullStrategy';path='/api/export/full-strategy'},
    [ordered]@{method='solver.export.strategy';path='/api/export/strategy'},
    [ordered]@{method='solver.export.tree';path='/api/export/tree'},
    [ordered]@{method='solver.dump.strategy';path='/api/dump-strategy'},
    [ordered]@{method='solver.dump.result';path='/api/dump-result'}
  );$chosen=$null;$treeText=$null;$validation=$null
  foreach($c in$candidates){try{$r=Invoke-Bridge $socket $c.method $c.path 'POST' $body 30000 $transcript;$payload=Read-Property $r 'payload' $r;$txt=ConvertTo-Json -InputObject $payload -Depth 100 -Compress;$v=Test-FullTreeText $txt;if($v.valid){$chosen=$c;$treeText=$txt;$validation=$v;break}}catch{}}
  if($null-eq$chosen){$hints=Get-FrontendExportHints $socket;$hints|ConvertTo-Json -Depth 20|Set-Content -LiteralPath(Join-Path$outputPath'frontend-export-hints.json') -Encoding UTF8;throw 'FULL_TREE_EXPORT_UNRESOLVED: no probed native export returned a tree containing both turn and river strategy nodes. Inspect frontend-export-hints.json and bridge-transcript.jsonl; do not treat this board as solved.'}
  $gzPath=Join-Path$outputPath'tree.json.gz';Write-GzipText $treeText $gzPath;$sha=(Get-FileHash -LiteralPath $gzPath -Algorithm SHA256).Hash.ToLowerInvariant();$bytes=(Get-Item -LiteralPath $gzPath).Length;$parts=@(Split-GitSafe $gzPath)
  $meta=[ordered]@{schema_version=1;format='texassolver-full-tree-json-gzip';board=$Board;full_tree_validated=$true;validation=$validation;export_method=$chosen.method;export_path=$chosen.path;gzip_sha256=$sha;gzip_bytes=$bytes;parts=$parts};$meta|ConvertTo-Json -Depth 20|Set-Content -LiteralPath(Join-Path$outputPath'tree.meta.json') -Encoding UTF8
  $run=[ordered]@{schema_version=3;runner_version=$ScriptVersion;board=$Board;board_ids=$boardIds;solver_exe=$solverPath;solver_sha256=(Get-FileHash -LiteralPath $solverPath -Algorithm SHA256).Hash.ToLowerInvariant();max_iterations=$MaxIterations;target_exploitability=$TargetExploitability;final_status=$status;full_tree_export=$meta;elapsed_ms=[int]([DateTime]::UtcNow-$runStarted).TotalMilliseconds};$run|ConvertTo-Json -Depth 30|Set-Content -LiteralPath(Join-Path$outputPath'run.json') -Encoding UTF8
  Write-Host "OK FULL TREE: $Board -> $($chosen.method); gzip=$bytes bytes"
}catch{if($null-ne$socket-and$socket.State-eq[Net.WebSockets.WebSocketState]::Open){try{Invoke-Bridge $socket 'solver.solve.stop' '/api/solve/stop' 'POST' @{} 5000 $transcript|Out-Null}catch{}};throw}finally{if($transcript.Count-gt0){$transcript|%{ConvertTo-CompactJson $_}|Set-Content -LiteralPath(Join-Path$outputPath'bridge-transcript.jsonl') -Encoding UTF8};if($null-ne$socket){try{$socket.Dispose()}catch{}};if($null-ne$process-and-not$process.HasExited){try{$process.CloseMainWindow()|Out-Null;if(-not$process.WaitForExit(3000)){$process.Kill()}}catch{}};if(-not$ShowHostWindow){try{[TsGpu.WindowHider]::Stop()}catch{}}}

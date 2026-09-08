[CmdletBinding()]
param(
    [string]$SolverExe = '',
    [string]$Config = '',
    [string]$Board = '6s As 8c',
    [string]$OutputDirectory = '',
    [int]$MaxIterations = 1000,
    [double]$TargetExploitability = 0.5,
    [int]$ExportMaxNodes = 100000,
    [int]$SolveTimeoutMinutes = 180
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $SolverExe) {
    $SolverExe = Join-Path $repoRoot '..\TexasSolverGpu-v0.2.0-windows-x64\TexasSolverGpu_131.exe'
}
if (-not $Config) {
    $Config = Join-Path $repoRoot 'smoke\CFG001-one-board.json'
}
if (-not $OutputDirectory) {
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
    $OutputDirectory = Join-Path $repoRoot "_diagnostics\full-tree-$stamp"
}

$solverPath = (Resolve-Path -LiteralPath $SolverExe).Path
$configPath = (Resolve-Path -LiteralPath $Config).Path
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
$workerOutput = Join-Path $outputPath 'worker'
[IO.Directory]::CreateDirectory($outputPath) | Out-Null

function ConvertTo-CompactJson([object]$Value, [int]$Depth = 100) {
    return (ConvertTo-Json -InputObject $Value -Depth $Depth -Compress)
}

function Read-Property([object]$Object, [string]$Name, [object]$Default = $null) {
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Wait-Task([System.Threading.Tasks.Task]$Task, [int]$TimeoutMs, [string]$What) {
    if (-not $Task.Wait($TimeoutMs)) { throw "Timeout while waiting for $What." }
    if ($Task.IsFaulted) { throw $Task.Exception.GetBaseException() }
    return $Task
}

function Receive-WebSocketText([System.Net.WebSockets.ClientWebSocket]$Socket, [int]$TimeoutMs) {
    $stream = [System.IO.MemoryStream]::new()
    try {
        do {
            $buffer = New-Object byte[] 65536
            $segment = [ArraySegment[byte]]::new($buffer)
            $cts = [System.Threading.CancellationTokenSource]::new($TimeoutMs)
            try {
                $task = $Socket.ReceiveAsync($segment, $cts.Token)
                Wait-Task $task $TimeoutMs 'DevTools response' | Out-Null
                $result = $task.Result
            } finally { $cts.Dispose() }
            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
                throw 'WebView2 DevTools socket closed unexpectedly.'
            }
            $stream.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)
        return [Text.Encoding]::UTF8.GetString($stream.ToArray())
    } finally { $stream.Dispose() }
}

$script:CdpId = 0
function Invoke-Cdp([System.Net.WebSockets.ClientWebSocket]$Socket, [string]$Method, [object]$Params, [int]$TimeoutMs = 120000) {
    $script:CdpId++
    $id = $script:CdpId
    $request = ConvertTo-CompactJson ([ordered]@{ id = $id; method = $Method; params = $Params })
    $bytes = [Text.Encoding]::UTF8.GetBytes($request)
    $send = $Socket.SendAsync([ArraySegment[byte]]::new($bytes), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None)
    Wait-Task $send $TimeoutMs 'DevTools send' | Out-Null
    while ($true) {
        $message = Receive-WebSocketText $Socket $TimeoutMs | ConvertFrom-Json
        $messageId = Read-Property $message 'id' $null
        if ($null -ne $messageId -and [int]$messageId -eq $id) {
            $messageError = Read-Property $message 'error' $null
            if ($null -ne $messageError) { throw "CDP $Method failed: $(ConvertTo-CompactJson $messageError)" }
            return (Read-Property $message 'result' $null)
        }
    }
}

function Invoke-JavaScript([System.Net.WebSockets.ClientWebSocket]$Socket, [string]$Expression, [int]$TimeoutMs = 120000) {
    $result = Invoke-Cdp $Socket 'Runtime.evaluate' ([ordered]@{
        expression = $Expression
        awaitPromise = $true
        returnByValue = $true
        userGesture = $true
    }) $TimeoutMs
    $exceptionDetails = Read-Property $result 'exceptionDetails' $null
    if ($null -ne $exceptionDetails) {
        throw "JavaScript failed: $(ConvertTo-CompactJson $exceptionDetails)"
    }
    $remoteObject = Read-Property $result 'result' $null
    return (Read-Property $remoteObject 'value' $null)
}

function New-BridgeBootstrap {
    return @'
(() => {
  if (window.__tsgpuPoc && typeof window.__tsgpuPoc.requestObject === 'function') return true;
  if (!window.chrome || !window.chrome.webview) throw new Error('Native WebView2 bridge is unavailable');
  const state = { seq: 1, pending: new Map(), token: null };
  window.chrome.webview.addEventListener('message', event => {
    let msg = event.data;
    if (typeof msg === 'string') { try { msg = JSON.parse(msg); } catch (_) { return; } }
    if (!msg || typeof msg.id !== 'string') return;
    const pending = state.pending.get(msg.id);
    if (!pending) return;
    clearTimeout(pending.timer);
    state.pending.delete(msg.id);
    pending.resolve(msg);
  });
  state.call = (method, params, timeoutMs) => new Promise((resolve, reject) => {
    const id = `diag_${Date.now()}_${state.seq++}`;
    const timer = setTimeout(() => { state.pending.delete(id); reject(new Error(`Bridge timeout: ${method}`)); }, timeoutMs);
    state.pending.set(id, { resolve, reject, timer });
    window.chrome.webview.postMessage(JSON.stringify({ id, method, params }));
  });
  state.request = async (method, path, httpMethod, body, timeoutMs) => {
    if (state.token === null) {
      const ping = await state.call('bridge.ping', {}, 3000);
      if (!ping.ok) throw new Error(`bridge.ping: ${JSON.stringify(ping.error)}`);
      state.token = (ping.result && typeof ping.result.bridge_token === 'string') ? ping.result.bridge_token : '';
    }
    const params = { apiBase: 'http://127.0.0.1:6006', path, method: httpMethod, bridge_token: state.token };
    if (body !== null && body !== undefined) params.body = body;
    let response = await state.call(method, params, timeoutMs);
    if (!response.ok && response.error && response.error.code === 'UNAUTHORIZED') {
      state.token = null;
      return state.request(method, path, httpMethod, body, timeoutMs);
    }
    if (!response.ok) throw new Error(`${method}: ${JSON.stringify(response.error)}`);
    return response.result;
  };
  state.requestObject = request => {
    const hasBody = Object.prototype.hasOwnProperty.call(request, 'body');
    return state.request(request.nativeMethod, request.path, request.httpMethod,
      hasBody ? request.body : undefined, Number(request.timeoutMs));
  };
  window.__tsgpuPoc = state;
  return true;
})()
'@
}

function Invoke-Bridge([System.Net.WebSockets.ClientWebSocket]$Socket, [string]$NativeMethod,
    [string]$Path, [string]$HttpMethod, [object]$Body, [int]$TimeoutMs,
    [System.Collections.Generic.List[object]]$Transcript) {
    $call = [ordered]@{
        nativeMethod = $NativeMethod
        path = $Path
        httpMethod = $HttpMethod
        timeoutMs = [int]$TimeoutMs
    }
    if ($null -ne $Body) { $call['body'] = $Body }
    $expression = "window.__tsgpuPoc.requestObject($(ConvertTo-CompactJson $call))"
    $started = [DateTime]::UtcNow
    try {
        $result = Invoke-JavaScript $Socket $expression ($TimeoutMs + 5000)
        $Transcript.Add([ordered]@{
            at = $started.ToString('o')
            method = $NativeMethod
            path = $Path
            body = $Body
            elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds
            result = 'ok'
        })
        return $result
    } catch {
        $Transcript.Add([ordered]@{
            at = $started.ToString('o')
            method = $NativeMethod
            path = $Path
            body = $Body
            elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds
            error = $_.Exception.Message
        })
        throw
    }
}

function Test-IsDescendant([int]$ProcessId, [int]$AncestorId, [hashtable]$ParentById) {
    $seen = @{}
    $current = $ProcessId
    while ($current -gt 0 -and -not $seen.ContainsKey($current)) {
        if ($current -eq $AncestorId) { return $true }
        $seen[$current] = $true
        if (-not $ParentById.ContainsKey($current)) { return $false }
        $current = [int]$ParentById[$current]
    }
    return $false
}

function Find-DebugPort([int]$SolverProcessId) {
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    while ([DateTime]::UtcNow -lt $deadline) {
        $processes = @(Get-CimInstance Win32_Process)
        $parentById = @{}
        foreach ($item in $processes) { $parentById[[int]$item.ProcessId] = [int]$item.ParentProcessId }
        foreach ($item in $processes) {
            $commandLine = [string]$item.CommandLine
            if ($commandLine -match '--remote-debugging-port=(\d+)' -and
                (Test-IsDescendant ([int]$item.ProcessId) $SolverProcessId $parentById)) {
                return [int]$Matches[1]
            }
        }
        Start-Sleep -Milliseconds 250
    }
    throw "Could not discover the WebView2 debug port below solver PID $SolverProcessId."
}

function Find-FirstChanceBoundary([object]$Node, [int[]]$RelativePath = @()) {
    if ($null -eq $Node) { return $null }
    if ([string](Read-Property $Node 'type' '') -eq 'chance') {
        return [pscustomobject]@{ Path = @($RelativePath); Node = $Node }
    }
    $childrenProperty = $Node.PSObject.Properties['childrens']
    if ($null -eq $childrenProperty) { return $null }
    $children = $childrenProperty.Value
    if ($children -is [System.Array]) {
        for ($i = 0; $i -lt $children.Count; $i++) {
            $found = Find-FirstChanceBoundary $children[$i] @($RelativePath + $i)
            if ($null -ne $found) { return $found }
        }
    }
    return $null
}

function Get-FirstPossibleCard([object]$PossibleResponse) {
    $maskValue = Read-Property $PossibleResponse 'possible_cards' $null
    if ($null -eq $maskValue) { throw 'solver.cards.possible response has no possible_cards field.' }
    $mask = [uint64]$maskValue
    $count = 0
    $first = -1
    for ($i = 0; $i -lt 52; $i++) {
        $bit = ([uint64]1 -shl $i)
        if (($mask -band $bit) -ne 0) {
            $count++
            if ($first -lt 0) { $first = $i }
        }
    }
    if ($first -lt 0) { throw 'solver.cards.possible returned an empty card set.' }
    return [pscustomobject]@{ Card = $first; Count = $count; Mask = $mask }
}

function Convert-CardIdToText([int]$CardId) {
    $ranks = '23456789TJQKA'
    $suits = 'cdhs'
    $rankIndex = [int][Math]::Floor($CardId / 4)
    return "$($ranks[$rankIndex])$($suits[$CardId % 4])"
}

function Assert-StreetFragment([object]$Node, [int]$ExpectedRound, [string]$Label) {
    $round = [int](Read-Property $Node 'betting round' -1)
    if ($round -ne $ExpectedRound) { throw "$Label export has betting round $round, expected $ExpectedRound." }
    if ([string](Read-Property $Node 'type' '') -ne 'action') { throw "$Label export root is not an action node." }
    $strategy = Read-Property $Node 'strategy' $null
    if ($null -eq $strategy) { throw "$Label export root has no strategy." }
    foreach ($field in @('card_strings', 'reach_probs', 'strategy_probs', 'action_evs', 'evs')) {
        if ($null -eq (Read-Property $strategy $field $null)) { throw "$Label strategy has no $field." }
    }
}

function Write-Utf8Json([object]$Value, [string]$Path, [int]$Depth = 100) {
    $json = ConvertTo-Json -InputObject $Value -Depth $Depth
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, $json, $utf8)
}

$beforeIds = @{}
foreach ($item in @(Get-Process -ErrorAction SilentlyContinue)) {
    try {
        if ([string]::Equals([IO.Path]::GetFullPath($item.Path), $solverPath, [StringComparison]::OrdinalIgnoreCase)) {
            $beforeIds[[int]$item.Id] = $true
        }
    } catch {}
}

$solverProcess = $null
$socket = $null
$transcript = [System.Collections.Generic.List[object]]::new()
try {
    $workerArgs = @{
        SolverExe = $solverPath
        Config = $configPath
        Board = $Board
        OutputDirectory = $workerOutput
        MaxIterations = $MaxIterations
        TargetExploitability = $TargetExploitability
        ExpectedBetAmount = 18
        ExpectedRaiseAmount = 73
        DecisionNode = 'BB_RESPONSE'
        ExportMaxNodes = $ExportMaxNodes
        SolveTimeoutMinutes = $SolveTimeoutMinutes
        KeepHost = $true
    }
    & (Join-Path $repoRoot 'tsgpu-worker.ps1') @workerArgs

    $candidates = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try {
            (-not $beforeIds.ContainsKey([int]$_.Id)) -and
            [string]::Equals([IO.Path]::GetFullPath($_.Path), $solverPath, [StringComparison]::OrdinalIgnoreCase)
        } catch { $false }
    } | Sort-Object StartTime -Descending)
    $solverProcess = $candidates | Select-Object -First 1
    if ($null -eq $solverProcess) { throw 'The worker did not leave a new solver host process running.' }

    $port = Find-DebugPort ([int]$solverProcess.Id)
    $http = [Net.WebClient]::new()
    try {
        $targets = @($http.DownloadString("http://127.0.0.1:$port/json/list") | ConvertFrom-Json)
    } finally { $http.Dispose() }
    $target = $targets | Where-Object { $_.type -eq 'page' -and $_.url -like 'https://appassets.local/*' } | Select-Object -First 1
    if ($null -eq $target) { throw "No appassets.local WebView target was found on port $port." }

    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp $socket 'Runtime.enable' @{} 10000 | Out-Null
    Invoke-JavaScript $socket (New-BridgeBootstrap) 10000 | Out-Null

    Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = @() }) 10000 $transcript | Out-Null
    $flopExport = Invoke-Bridge $socket 'solver.export.currentStreet' '/api/export/current-street' 'POST' ([ordered]@{
        history = @()
        max_nodes = $ExportMaxNodes
    }) 120000 $transcript
    Write-Utf8Json $flopExport (Join-Path $outputPath 'flop.response.json')
    $flop = Read-Property $flopExport 'payload' $flopExport
    Write-Utf8Json $flop (Join-Path $outputPath 'flop.native.json')
    Write-Host "Flop response: type=$([string](Read-Property $flop 'type' '<missing>')), round=$(Read-Property $flop 'betting round' '<missing>')"
    Assert-StreetFragment $flop 1 'Flop'
    $flopBoundary = Find-FirstChanceBoundary $flop
    if ($null -eq $flopBoundary) { throw 'Flop street export contains no chance boundary.' }
    if (@((Read-Property $flopBoundary.Node 'childrens' @{}).PSObject.Properties).Count -ne 0) {
        throw 'Flop current-street export unexpectedly crossed its chance boundary.'
    }

    $flopChanceHistory = @($flopBoundary.Path)
    Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $flopChanceHistory }) 10000 $transcript | Out-Null
    $turnCardSet = Get-FirstPossibleCard (Invoke-Bridge $socket 'solver.cards.possible' '/api/possible-cards' 'GET' $null 10000 $transcript)
    $turnHistory = @($flopChanceHistory + [int]$turnCardSet.Card)

    $turnExport = Invoke-Bridge $socket 'solver.export.currentStreet' '/api/export/current-street' 'POST' ([ordered]@{
        history = $turnHistory
        max_nodes = $ExportMaxNodes
    }) 120000 $transcript
    $turn = Read-Property $turnExport 'payload' $turnExport
    Assert-StreetFragment $turn 2 'Turn'
    $turnBoundary = Find-FirstChanceBoundary $turn
    if ($null -eq $turnBoundary) { throw 'Turn street export contains no chance boundary.' }

    $turnChanceHistory = @($turnHistory + @($turnBoundary.Path))
    Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $turnChanceHistory }) 10000 $transcript | Out-Null
    $riverCardSet = Get-FirstPossibleCard (Invoke-Bridge $socket 'solver.cards.possible' '/api/possible-cards' 'GET' $null 10000 $transcript)
    $riverHistory = @($turnChanceHistory + [int]$riverCardSet.Card)

    $riverExport = Invoke-Bridge $socket 'solver.export.currentStreet' '/api/export/current-street' 'POST' ([ordered]@{
        history = $riverHistory
        max_nodes = $ExportMaxNodes
    }) 120000 $transcript
    $river = Read-Property $riverExport 'payload' $riverExport
    Assert-StreetFragment $river 3 'River'

    Write-Utf8Json $flop (Join-Path $outputPath 'flop.native.json')
    Write-Utf8Json $turn (Join-Path $outputPath 'turn.native.json')
    Write-Utf8Json $river (Join-Path $outputPath 'river.native.json')

    $proof = [ordered]@{
        schema_version = 1
        diagnostic = 'confirmed-current-street-chain'
        created_at_utc = [DateTime]::UtcNow.ToString('o')
        solver_exe = $solverPath
        solver_sha256 = (Get-FileHash -LiteralPath $solverPath -Algorithm SHA256).Hash.ToLowerInvariant()
        board = $Board
        export_method = 'solver.export.currentStreet'
        export_endpoint = 'POST /api/export/current-street'
        history_method = 'solver.history.apply'
        legal_cards_method = 'solver.cards.possible'
        flop = [ordered]@{
            history = @()
            round = 1
            chance_history = $flopChanceHistory
            node_count = Read-Property $flopExport 'node_count' $null
        }
        turn = [ordered]@{
            card_id = [int]$turnCardSet.Card
            card = Convert-CardIdToText ([int]$turnCardSet.Card)
            legal_card_count = [int]$turnCardSet.Count
            history = $turnHistory
            round = 2
            chance_history = $turnChanceHistory
            node_count = Read-Property $turnExport 'node_count' $null
        }
        river = [ordered]@{
            card_id = [int]$riverCardSet.Card
            card = Convert-CardIdToText ([int]$riverCardSet.Card)
            legal_card_count = [int]$riverCardSet.Count
            history = $riverHistory
            round = 3
            node_count = Read-Property $riverExport 'node_count' $null
        }
        strategy_fields_verified = @('card_strings', 'reach_probs', 'strategy_probs', 'action_evs', 'evs')
        result = 'PASS'
    }
    Write-Utf8Json $proof (Join-Path $outputPath 'proof.json')
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $transcriptLines = @($transcript | ForEach-Object { ConvertTo-CompactJson $_ })
    [IO.File]::WriteAllLines((Join-Path $outputPath 'bridge-transcript.jsonl'), $transcriptLines, $utf8)

    Write-Host ''
    Write-Host 'FULL-TREE MECHANISM DIAGNOSTIC: PASS'
    Write-Host "Flop export -> turn $($proof.turn.card) -> river $($proof.river.card)"
    Write-Host "Proof: $(Join-Path $outputPath 'proof.json')"
} finally {
    if ($transcript.Count -gt 0) {
        try {
            $utf8 = New-Object System.Text.UTF8Encoding($false)
            $transcriptLines = @($transcript | ForEach-Object { ConvertTo-CompactJson $_ })
            [IO.File]::WriteAllLines((Join-Path $outputPath 'bridge-transcript.jsonl'), $transcriptLines, $utf8)
        } catch {}
    }
    if ($null -ne $socket) { try { $socket.Dispose() } catch {} }
    if ($null -ne $solverProcess) {
        try {
            $live = Get-Process -Id $solverProcess.Id -ErrorAction SilentlyContinue
            if ($null -ne $live) {
                $live.CloseMainWindow() | Out-Null
                if (-not $live.WaitForExit(3000)) { $live.Kill() }
            }
        } catch {}
    }
}

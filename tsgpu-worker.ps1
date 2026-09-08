[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SolverExe,
    [Parameter(Mandatory = $true)][string]$Config,
    [Parameter(Mandatory = $true)][string]$Board,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [int]$MaxIterations = 1000,
    [double]$TargetExploitability = 0.5,
    [int]$ExpectedBetAmount = 0,
    [int]$ExpectedRaiseAmount = 0,
    [ValidateSet('BB_RESPONSE', 'UTG_CBET', 'UTG_OOP_CBET', 'BTN_RESPONSE', 'BTN_STAB', 'UTG_RESPONSE')][string]$DecisionNode = 'BB_RESPONSE',
    [int]$ExportMaxNodes = 2000000,
    [int]$SolveTimeoutMinutes = 180,
    [switch]$ShowHostWindow,
    [switch]$KeepHost
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ScriptVersion = 'v020-fulltree'
$StatusRetryLimit = 3

# The host can call ShowWindow after ProcessStartInfo has requested Hidden.
# Install an out-of-context WinEvent hook on a dedicated message-pump thread
# before launching it, then keep an EnumWindows fallback active for the entire
# solve. This affects only windows owned by the exact solver executable path.
if (-not ('TsGpu.WindowSuppressor' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace TsGpu {
    public static class WindowSuppressor {
        private const uint EventObjectShow = 0x8002;
        private const uint WineventOutOfContext = 0x0000;
        private const uint WineventSkipOwnProcess = 0x0002;
        private const uint ProcessQueryLimitedInformation = 0x1000;
        private const uint PmRemove = 0x0001;

        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        private delegate void WinEventProc(IntPtr hook, uint eventType, IntPtr hWnd,
            int objectId, int childId, uint eventThread, uint eventTime);

        [StructLayout(LayoutKind.Sequential)]
        private struct Point { public int X; public int Y; }

        [StructLayout(LayoutKind.Sequential)]
        private struct Message {
            public IntPtr HWnd;
            public uint Value;
            public UIntPtr WParam;
            public IntPtr LParam;
            public uint Time;
            public Point Pt;
        }

        private static volatile bool running;
        private static volatile int targetProcessId;
        private static string targetPath;
        private static Thread thread;
        private static ManualResetEvent ready;
        private static IntPtr hook;
        private static WinEventProc eventCallback;
        private static EnumWindowsProc enumCallback;

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        private static extern IntPtr SetWinEventHook(uint eventMin, uint eventMax,
            IntPtr module, WinEventProc callback, uint processId, uint threadId, uint flags);

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool UnhookWinEvent(IntPtr eventHook);

        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool PeekMessage(out Message message, IntPtr hWnd,
            uint filterMin, uint filterMax, uint removeMessage);

        [DllImport("user32.dll")]
        private static extern bool TranslateMessage(ref Message message);

        [DllImport("user32.dll")]
        private static extern IntPtr DispatchMessage(ref Message message);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(uint access, bool inheritHandle, uint processId);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool QueryFullProcessImageName(IntPtr process, uint flags,
            StringBuilder path, ref int size);

        [DllImport("kernel32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr handle);

        public static void Start(string executablePath) {
            Stop();
            targetPath = Path.GetFullPath(executablePath);
            targetProcessId = 0;
            ready = new ManualResetEvent(false);
            running = true;
            thread = new Thread(new ThreadStart(Pump));
            thread.IsBackground = true;
            thread.Name = "TexasSolverGPU window suppressor";
            thread.Start();
            if (!ready.WaitOne(3000)) {
                running = false;
                throw new InvalidOperationException("Window suppressor did not start.");
            }
        }

        public static void Stop() {
            running = false;
            Thread oldThread = thread;
            if (oldThread != null && oldThread.IsAlive) oldThread.Join(2000);
            thread = null;
            targetProcessId = 0;
            if (ready != null) { ready.Close(); ready = null; }
        }

        public static void SetTargetProcessId(int processId) {
            targetProcessId = processId;
        }

        private static void Pump() {
            eventCallback = new WinEventProc(OnWindowEvent);
            enumCallback = new EnumWindowsProc(OnEnumeratedWindow);
            hook = SetWinEventHook(EventObjectShow, EventObjectShow, IntPtr.Zero,
                eventCallback, 0, 0, WineventOutOfContext | WineventSkipOwnProcess);
            ready.Set();
            try {
                while (running) {
                    Message message;
                    while (PeekMessage(out message, IntPtr.Zero, 0, 0, PmRemove)) {
                        TranslateMessage(ref message);
                        DispatchMessage(ref message);
                    }
                    EnumWindows(enumCallback, IntPtr.Zero);
                    Thread.Sleep(25);
                }
            } finally {
                if (hook != IntPtr.Zero) UnhookWinEvent(hook);
                hook = IntPtr.Zero;
                eventCallback = null;
                enumCallback = null;
            }
        }

        private static void OnWindowEvent(IntPtr eventHook, uint eventType, IntPtr hWnd,
            int objectId, int childId, uint eventThread, uint eventTime) {
            HideIfTarget(hWnd);
        }

        private static bool OnEnumeratedWindow(IntPtr hWnd, IntPtr lParam) {
            HideIfTarget(hWnd);
            return true;
        }

        private static void HideIfTarget(IntPtr hWnd) {
            if (hWnd == IntPtr.Zero || String.IsNullOrEmpty(targetPath)) return;
            uint processId;
            GetWindowThreadProcessId(hWnd, out processId);
            if (processId == 0) return;
            int knownProcessId = targetProcessId;
            if (knownProcessId != 0) {
                if (processId != (uint)knownProcessId) return;
            } else if (!IsTargetProcess(processId)) {
                return;
            }
            ShowWindowAsync(hWnd, 0);
        }

        private static bool IsTargetProcess(uint processId) {
            IntPtr process = OpenProcess(ProcessQueryLimitedInformation, false, processId);
            if (process == IntPtr.Zero) return false;
            try {
                int capacity = 32768;
                StringBuilder path = new StringBuilder(capacity);
                if (!QueryFullProcessImageName(process, 0, path, ref capacity)) return false;
                return String.Equals(Path.GetFullPath(path.ToString()), targetPath,
                    StringComparison.OrdinalIgnoreCase);
            } catch {
                return false;
            } finally {
                CloseHandle(process);
            }
        }
    }
}
'@
}

function ConvertTo-CompactJson([object]$Value, [int]$Depth = 100) {
    # -InputObject preserves arrays (including null elements) in Windows
    # PowerShell 5.1. Piping an array enumerates it and drops a null element.
    return (ConvertTo-Json -InputObject $Value -Depth $Depth -Compress)
}

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    try { return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port }
    finally { $listener.Stop() }
}

function Convert-CardToId([string]$Card) {
    if ($Card -notmatch '^[2-9TJQKA][cdhs]$') { throw "Invalid card: $Card" }
    $rank = '23456789TJQKA'.IndexOf($Card.Substring(0, 1).ToUpperInvariant())
    $suit = 'cdhs'.IndexOf($Card.Substring(1, 1).ToLowerInvariant())
    return ($rank * 4 + $suit)
}

function Convert-Board([string]$Text) {
    $tokens = @($Text -split '[\s,]+' | Where-Object { $_ })
    if ($tokens.Count -ne 3) { throw 'Each board line must contain exactly one three-card flop.' }
    $ids = @($tokens | ForEach-Object { Convert-CardToId $_ })
    if (@($ids | Select-Object -Unique).Count -ne 3) { throw 'Board contains duplicate cards.' }
    return $ids
}

function Convert-Sizing([object]$Value) {
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    $items = @($text.Replace(';', ',') -split '[\s,|/]+' | ForEach-Object {
        $v = $_.Trim().ToLowerInvariant()
        if ($v) {
            if ($v -match '^\d+(\.\d+)?$') { "$v%" } else { $v }
        }
    })
    return ($items -join ',')
}

function Read-Property([object]$Object, [string]$Name, [object]$Default = $null) {
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Convert-ToNativeConfig([object]$InputConfig, [int[]]$BoardIds) {
    $c = Read-Property $InputConfig 'config' $InputConfig
    $oopRange = @(Read-Property $c 'oopRange' @())
    $ipRange = @(Read-Property $c 'ipRange' @())
    if ($oopRange.Count -ne 1326) { throw "oopRange must contain 1326 values; got $($oopRange.Count)." }
    if ($ipRange.Count -ne 1326) { throw "ipRange must contain 1326 values; got $($ipRange.Count)." }

    return [ordered]@{
        oop_range = $oopRange
        ip_range = $ipRange
        board = $BoardIds
        starting_pot = [double](Read-Property $c 'startingPot' 0)
        effective_stack = [double](Read-Property $c 'effectiveStack' 0)
        rake_rate = [double](Read-Property $c 'rakeRate' 0)
        rake_cap = [double](Read-Property $c 'rakeCap' 0)
        oop_flop_bet = (Convert-Sizing (Read-Property $c 'oopFlopBet' ''))
        oop_flop_raise = (Convert-Sizing (Read-Property $c 'oopFlopRaise' ''))
        ip_flop_bet = (Convert-Sizing (Read-Property $c 'ipFlopBet' ''))
        ip_flop_raise = (Convert-Sizing (Read-Property $c 'ipFlopRaise' ''))
        oop_turn_bet = (Convert-Sizing (Read-Property $c 'oopTurnBet' ''))
        oop_turn_raise = (Convert-Sizing (Read-Property $c 'oopTurnRaise' ''))
        ip_turn_bet = (Convert-Sizing (Read-Property $c 'ipTurnBet' ''))
        ip_turn_raise = (Convert-Sizing (Read-Property $c 'ipTurnRaise' ''))
        oop_river_bet = (Convert-Sizing (Read-Property $c 'oopRiverBet' ''))
        oop_river_raise = (Convert-Sizing (Read-Property $c 'oopRiverRaise' ''))
        ip_river_bet = (Convert-Sizing (Read-Property $c 'ipRiverBet' ''))
        ip_river_raise = (Convert-Sizing (Read-Property $c 'ipRiverRaise' ''))
        donk_option = $true
        oop_turn_donk = (Convert-Sizing (Read-Property $c 'oopTurnDonk' ''))
        oop_river_donk = (Convert-Sizing (Read-Property $c 'oopRiverDonk' ''))
        max_raise_number = [Math]::Max(0, [Math]::Min(255, [int](Read-Property $c 'maxRaiseNumber' 3)))
        add_allin_threshold = [Math]::Max(0, [double](Read-Property $c 'addAllinThreshold' 0) / 100.0)
        force_allin_threshold = 0.2
        add_allin_flop_ip = [bool](Read-Property $c 'addAllinFlopIp' $false)
        add_allin_turn_ip = [bool](Read-Property $c 'addAllinTurnIp' $false)
        add_allin_river_ip = [bool](Read-Property $c 'addAllinRiverIp' $false)
        add_allin_flop_oop = [bool](Read-Property $c 'addAllinFlopOop' $false)
        add_allin_turn_oop = [bool](Read-Property $c 'addAllinTurnOop' $false)
        add_allin_river_oop = [bool](Read-Property $c 'addAllinRiverOop' $false)
        merging_threshold = 0.1
        num_players = 2
    }
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
  if (window.__tsgpuPoc) return true;
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
    const id = `poc_${Date.now()}_${state.seq++}`;
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
    // Match the stock frontend exactly: JSON.stringify must omit `body` for
    // bodyless GET requests. Sending `body: null` makes the v0.2.0 native
    // handler fail to post a response for solver.solve.status.
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
    return state.request(
      request.nativeMethod,
      request.path,
      request.httpMethod,
      hasBody ? request.body : undefined,
      Number(request.timeoutMs)
    );
  };
  window.__tsgpuPoc = state;
  return true;
})()
'@
}

function Invoke-Bridge([System.Net.WebSockets.ClientWebSocket]$Socket, [string]$NativeMethod, [string]$Path, [string]$HttpMethod, [object]$Body, [int]$TimeoutMs, [System.Collections.Generic.List[object]]$Transcript) {
    # Use a named object instead of a positional JSON array. On Windows
    # PowerShell 5.1, piping the old array through ConvertTo-Json removed its
    # null body element. timeoutMs then shifted into `body`, while JavaScript
    # received undefined for timeoutMs and fired its timer immediately.
    $call = [ordered]@{
        nativeMethod = $NativeMethod
        path = $Path
        httpMethod = $HttpMethod
        timeoutMs = [int]$TimeoutMs
    }
    if ($null -ne $Body) { $call['body'] = $Body }
    $callJson = ConvertTo-CompactJson -Value $call
    $expression = "window.__tsgpuPoc.requestObject($callJson)"
    $started = [DateTime]::UtcNow
    try {
        $result = Invoke-JavaScript $Socket $expression ($TimeoutMs + 5000)
        $rawResults = Read-Property $result 'results' $null
        $payload = Read-Property $result 'payload' $null
        $rawActions = Read-Property $result 'actions' $null
        $summary = if ($null -ne $rawResults) { "results[$(@($rawResults).Count)]" } elseif ($null -ne $payload) { 'payload' } elseif ($null -ne $rawActions) { "actions: $rawActions" } else { 'ok' }
        $Transcript.Add([ordered]@{ at = $started.ToString('o'); method = $NativeMethod; path = $Path; body = $Body; timeout_ms = $TimeoutMs; elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds; result = $summary })
        return $result
    } catch {
        $Transcript.Add([ordered]@{ at = $started.ToString('o'); method = $NativeMethod; path = $Path; body = $Body; timeout_ms = $TimeoutMs; elapsed_ms = [int]([DateTime]::UtcNow - $started).TotalMilliseconds; error = $_.Exception.Message })
        throw
    }
}

function Split-Actions([object]$Response) {
    $text = [string](Read-Property $Response 'actions' '')
    return @($text -split '/' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Find-ActionIndex([string[]]$Actions, [string]$Kind, [Nullable[int]]$Amount) {
    $candidates = @(for ($i = 0; $i -lt $Actions.Count; $i++) {
        # actionsAfter uses labels such as Check:0 and Bet:18, while exported
        # valid_actions may use Fold, Call and Raise 73. Accept both separators.
        if ($Actions[$i] -match "(?i)^$([regex]::Escape($Kind))(?:(?:\s+|:)\s*(-?\d+(?:\.\d+)?))?$") {
            [pscustomobject]@{ Index = $i; Label = $Actions[$i]; Amount = if ($Matches[1]) { [double]$Matches[1] } else { $null } }
        }
    })
    if ($null -ne $Amount -and $candidates.Count -gt 0) {
        # Windows PowerShell exposes a populated Nullable[int] as Int32, so
        # accessing .Value fails under StrictMode. Compare its numeric value directly.
        $requestedAmount = [double]$Amount
        $exact = @($candidates | Where-Object { $null -ne $_.Amount -and [Math]::Abs([double]$_.Amount - $requestedAmount) -lt 0.001 })
        if ($exact.Count -eq 1) { return $exact[0] }
    }
    if ($candidates.Count -eq 1) { return $candidates[0] }
    throw "Cannot select $Kind $Amount from actions: $($Actions -join ' / ')"
}

function Get-ActionSlot([string[]]$Actions, [string]$Kind) {
    for ($i = 0; $i -lt $Actions.Count; $i++) {
        if ($Actions[$i] -match "(?i)^$([regex]::Escape($Kind))(?:(?:\s+|:)|$)") { return $i }
    }
    throw "Required $Kind action is missing: $($Actions -join ' / ')"
}

function Test-FullTreeJson([string]$Json) {
    $hasChildren = $Json -match '"childrens"'
    $hasStrategy = $Json -match '"strategy"'
    $hasTurn = ($Json -match '"betting round"\s*:\s*2') -or ($Json -match '"betting_round"\s*:\s*2')
    $hasRiver = ($Json -match '"betting round"\s*:\s*3') -or ($Json -match '"betting_round"\s*:\s*3')
    return [pscustomobject]@{
        valid = ($hasChildren -and $hasStrategy -and $hasTurn -and $hasRiver)
        has_children = $hasChildren
        has_strategy = $hasStrategy
        has_turn = $hasTurn
        has_river = $hasRiver
    }
}

function Write-GzipUtf8([string]$Text, [string]$Path) {
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $gzip = [IO.Compression.GZipStream]::new($stream, [IO.Compression.CompressionLevel]::Optimal, $false)
        try {
            $writer = [IO.StreamWriter]::new($gzip, [Text.UTF8Encoding]::new($false))
            try { $writer.Write($Text) } finally { $writer.Dispose() }
        } finally { $gzip.Dispose() }
    } finally { $stream.Dispose() }
}

function Split-GitSafe([string]$Path, [int64]$MaxBytes = 90000000) {
    $file = Get-Item -LiteralPath $Path
    if ($file.Length -le $MaxBytes) { return @($file.Name) }
    $parts = [Collections.Generic.List[string]]::new()
    $source = [IO.File]::OpenRead($Path)
    try {
        $index = 1
        while ($source.Position -lt $source.Length) {
            $name = ([IO.Path]::GetFileName($Path) + ('.part{0:D3}' -f $index))
            $destinationPath = Join-Path ([IO.Path]::GetDirectoryName($Path)) $name
            $destination = [IO.File]::Create($destinationPath)
            try {
                $remaining = [Math]::Min($MaxBytes, $source.Length - $source.Position)
                $buffer = New-Object byte[] 1048576
                while ($remaining -gt 0) {
                    $count = $source.Read($buffer, 0, [int][Math]::Min($buffer.Length, $remaining))
                    if ($count -le 0) { break }
                    $destination.Write($buffer, 0, $count)
                    $remaining -= $count
                }
            } finally { $destination.Dispose() }
            $parts.Add($name)
            $index++
        }
    } finally { $source.Dispose() }
    Remove-Item -LiteralPath $Path -Force
    return $parts.ToArray()
}
$solverPath = (Resolve-Path -LiteralPath $SolverExe).Path
$configPath = (Resolve-Path -LiteralPath $Config).Path
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($outputPath) | Out-Null
$boardIds = @(Convert-Board $Board)
$inputConfig = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$nativeConfig = Convert-ToNativeConfig $inputConfig $boardIds
$transcript = [System.Collections.Generic.List[object]]::new()
$port = Get-FreeTcpPort
$process = $null
$socket = $null
$runStarted = [DateTime]::UtcNow

try {
    if (-not $ShowHostWindow) {
        [TsGpu.WindowSuppressor]::Start($solverPath)
    }
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $solverPath
    $start.WorkingDirectory = [IO.Path]::GetDirectoryName($solverPath)
    $start.UseShellExecute = $false
    $start.CreateNoWindow = -not $ShowHostWindow
    $start.WindowStyle = if ($ShowHostWindow) { [Diagnostics.ProcessWindowStyle]::Normal } else { [Diagnostics.ProcessWindowStyle]::Hidden }
    $start.EnvironmentVariables['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = "--remote-debugging-port=$port --remote-allow-origins=http://127.0.0.1:$port"
    $process = [Diagnostics.Process]::Start($start)
    if ($null -eq $process) { throw 'Failed to launch solver process.' }
    if (-not $ShowHostWindow) {
        [TsGpu.WindowSuppressor]::SetTargetProcessId($process.Id)
    }

    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    $target = $null
    # System.Net.Http is not loaded by default in some Windows PowerShell 5.1
    # installations. WebClient is available in the base framework and is
    # sufficient for the loopback DevTools discovery request.
    $http = [Net.WebClient]::new()
    try {
        while ([DateTime]::UtcNow -lt $deadline -and $null -eq $target) {
            if ($process.HasExited) { throw "Solver exited during startup with code $($process.ExitCode)." }
            try {
                $json = $http.DownloadString("http://127.0.0.1:$port/json/list")
                $targets = @($json | ConvertFrom-Json)
                $target = $targets | Where-Object { $_.type -eq 'page' -and ($_.url -like 'https://appassets.local/*' -or $_.url -like '*index.html*') } | Select-Object -First 1
                if ($null -eq $target) { $target = $targets | Where-Object { $_.type -eq 'page' } | Select-Object -First 1 }
            } catch { Start-Sleep -Milliseconds 250 }
        }
    } finally { $http.Dispose() }
    if ($null -eq $target) { throw 'WebView2 DevTools endpoint did not expose an application page. Check WebView2 policy and runtime.' }

    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp $socket 'Runtime.enable' @{} 10000 | Out-Null
    Invoke-JavaScript $socket (New-BridgeBootstrap) 10000 | Out-Null
    Write-Host "WebView target: $($target.url)"

    Invoke-Bridge $socket 'solver.init' '/api/init' 'POST' $nativeConfig 120000 $transcript | Out-Null
    Invoke-Bridge $socket 'solver.allocate' '/api/allocate' 'POST' ([ordered]@{ enable_compression = $false }) 120000 $transcript | Out-Null
    # Verify the bodyless GET bridge schema before starting a long GPU solve.
    $preSolveStatus = Invoke-Bridge $socket 'solver.solve.status' '/api/solve/status' 'GET' $null 5000 $transcript
    Write-Host "Preflight status: phase=$(Read-Property $preSolveStatus 'phase' 'unknown'), running=$(Read-Property $preSolveStatus 'running' $false)"
    # Force the floating-point overload. Math.Max(0, 0.5) selected an integer
    # overload in Windows PowerShell 5.1 and silently sent zero to the solver.
    $targetExploitabilityValue = [Math]::Max([double]0.0, [double]$TargetExploitability)
    $solveBody = [ordered]@{ max_iterations = [Math]::Max(1, $MaxIterations); target_exploitability = $targetExploitabilityValue; compute_initial_exploitability = $true; verbose = $false }
    Invoke-Bridge $socket 'solver.solve.start' '/api/gpu-solve' 'POST' $solveBody 30000 $transcript | Out-Null

    $solveDeadline = [DateTime]::UtcNow.AddMinutes($SolveTimeoutMinutes)
    $status = $null
    $seenRunning = $false
    $statusStarted = [DateTime]::UtcNow
    $consecutiveStatusTimeouts = 0
    # These values are used by the do/while condition even when the first
    # status request times out and the catch block executes `continue`.
    $running = $true
    $terminalPhase = $false
    $startupGraceElapsed = $false
    do {
        Start-Sleep -Milliseconds 500
        try {
            $status = Invoke-Bridge $socket 'solver.solve.status' '/api/solve/status' 'GET' $null 5000 $transcript
            $consecutiveStatusTimeouts = 0
        } catch {
            if ($_.Exception.Message -like '*Bridge timeout: solver.solve.status*') {
                $consecutiveStatusTimeouts++
                Write-Warning "solver.solve.status timed out; solve is left running (retry $consecutiveStatusTimeouts/$StatusRetryLimit)."
                if ([DateTime]::UtcNow -ge $solveDeadline) { throw "Solve exceeded $SolveTimeoutMinutes minutes while status was unavailable." }
                if ($consecutiveStatusTimeouts -ge $StatusRetryLimit) { throw "solver.solve.status did not respond after $StatusRetryLimit consecutive retries." }
                continue
            }
            throw
        }
        if ((Read-Property $status 'phase' '') -eq 'error' -or (Read-Property $status 'last_error' '')) {
            throw "Native solve failed: $(Read-Property $status 'last_error' (ConvertTo-CompactJson $status))"
        }
        if ([DateTime]::UtcNow -ge $solveDeadline) { throw "Solve exceeded $SolveTimeoutMinutes minutes." }
        $running = [bool](Read-Property $status 'running' $false)
        if ($running) { $seenRunning = $true }
        $phase = ([string](Read-Property $status 'phase' '')).ToLowerInvariant()
        $terminalPhase = $phase -in @('done', 'finished', 'completed', 'solved')
        $startupGraceElapsed = ([DateTime]::UtcNow - $statusStarted).TotalSeconds -ge 5
    } while ($running -or (-not $seenRunning -and -not $terminalPhase -and -not $startupGraceElapsed))

    Invoke-Bridge $socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = @() }) 10000 $transcript | Out-Null

    $commonBody = [ordered]@{ history = @(); max_nodes = $ExportMaxNodes; dump_rounds = 2 }
    $currentStreetBody = [ordered]@{ history = @(); max_nodes = $ExportMaxNodes }
    $candidates = @(
        [ordered]@{ method = 'solver.export.currentStreet'; path = '/api/export/current-street'; body = $currentStreetBody },
        [ordered]@{ method = 'solver.export.fullTree'; path = '/api/export/full-tree'; body = $commonBody },
        [ordered]@{ method = 'solver.export.allStreets'; path = '/api/export/all-streets'; body = $commonBody },
        [ordered]@{ method = 'solver.export.fullStrategy'; path = '/api/export/full-strategy'; body = $commonBody },
        [ordered]@{ method = 'solver.export.strategy'; path = '/api/export/strategy'; body = $commonBody },
        [ordered]@{ method = 'solver.export.tree'; path = '/api/export/tree'; body = $commonBody },
        [ordered]@{ method = 'solver.dump.strategy'; path = '/api/dump-strategy'; body = ([ordered]@{ dump_rounds = 2 }) },
        [ordered]@{ method = 'solver.dump.result'; path = '/api/dump-result'; body = ([ordered]@{ dump_rounds = 2 }) }
    )
    $chosen = $null
    $treeText = $null
    $validation = $null
    $probeResults = [Collections.Generic.List[object]]::new()
    foreach ($candidate in $candidates) {
        try {
            $response = Invoke-Bridge $socket $candidate.method $candidate.path 'POST' $candidate.body 30000 $transcript
            $payload = Read-Property $response 'payload' $response
            if ($payload -is [string] -and $payload.TrimStart().StartsWith('{')) {
                $text = [string]$payload
            } else {
                $text = ConvertTo-Json -InputObject $payload -Depth 100 -Compress
            }
            $test = Test-FullTreeJson $text
            $probeResults.Add([ordered]@{ method = $candidate.method; path = $candidate.path; validation = $test })
            if ($test.valid) {
                $chosen = $candidate
                $treeText = $text
                $validation = $test
                break
            }
        } catch {
            $probeResults.Add([ordered]@{ method = $candidate.method; path = $candidate.path; error = $_.Exception.Message })
        }
    }
    $probeResults | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $outputPath 'export-probes.json') -Encoding UTF8
    if ($null -eq $chosen) {
        throw 'FULL_TREE_EXPORT_UNRESOLVED: the solved board is NOT accepted because no probed export contained both turn and river strategy nodes. Inspect export-probes.json and bridge-transcript.jsonl.'
    }

    $gzipPath = Join-Path $outputPath 'tree.json.gz'
    Write-GzipUtf8 $treeText $gzipPath
    $gzipSha = (Get-FileHash -LiteralPath $gzipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $gzipBytes = (Get-Item -LiteralPath $gzipPath).Length
    $parts = @(Split-GitSafe $gzipPath)
    $treeMeta = [ordered]@{
        schema_version = 1
        format = 'texassolver-full-tree-json-gzip'
        board = $Board
        full_tree_validated = $true
        validation = $validation
        export_method = $chosen.method
        export_path = $chosen.path
        gzip_sha256 = $gzipSha
        gzip_bytes = $gzipBytes
        parts = $parts
    }
    $treeMeta | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $outputPath 'tree.meta.json') -Encoding UTF8

    $run = [ordered]@{
        schema_version = 3
        runner_version = $ScriptVersion
        solver_exe = $solverPath
        solver_sha256 = (Get-FileHash -LiteralPath $solverPath -Algorithm SHA256).Hash.ToLowerInvariant()
        board = $Board
        board_ids = $boardIds
        max_iterations = $MaxIterations
        target_exploitability = $TargetExploitability
        final_status = $status
        full_tree_export = $treeMeta
        elapsed_ms = [int]([DateTime]::UtcNow - $runStarted).TotalMilliseconds
    }
    $run | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $outputPath 'run.json') -Encoding UTF8
    Write-Host "OK FULL TREE: $Board -> $($chosen.method), gzip=$gzipBytes bytes"
    Write-Host "Output: $outputPath"
} catch {
    if ($null -ne $socket -and $socket.State -eq [Net.WebSockets.WebSocketState]::Open) {
        try { Invoke-Bridge $socket 'solver.solve.stop' '/api/solve/stop' 'POST' @{} 5000 $transcript | Out-Null } catch {}
    }
    if ($transcript.Count -gt 0) {
        $transcript | ForEach-Object { ConvertTo-CompactJson $_ } | Set-Content -LiteralPath (Join-Path $outputPath 'bridge-transcript.jsonl') -Encoding UTF8
    }
    throw
} finally {
    if ($null -ne $socket) {
        try { $socket.Dispose() } catch {}
    }
    if ($null -ne $process -and -not $KeepHost -and -not $process.HasExited) {
        try { $process.CloseMainWindow() | Out-Null; if (-not $process.WaitForExit(3000)) { $process.Kill() } } catch {}
    }
    if (-not $ShowHostWindow) {
        try { [TsGpu.WindowSuppressor]::Stop() } catch {}
    }
}


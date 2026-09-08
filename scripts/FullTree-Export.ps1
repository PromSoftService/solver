Set-StrictMode -Version Latest

function Get-TsGpuProperty([object]$Object, [string]$Name, [object]$Default = $null) {
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function ConvertTo-TsGpuCompactJson([object]$Value, [int]$Depth = 100) {
    return (ConvertTo-Json -InputObject $Value -Depth $Depth -Compress)
}

function Get-TsGpuSha256Bytes([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Get-TsGpuHistoryKey([int[]]$History) {
    if ($History.Count -eq 0) { return 'root' }
    return ($History -join ',')
}

function Convert-TsGpuCardIdToText([int]$CardId) {
    if ($CardId -lt 0 -or $CardId -ge 52) { throw "Invalid card id: $CardId" }
    $ranks = '23456789TJQKA'
    $suits = 'cdhs'
    $rankIndex = [int][Math]::Floor($CardId / 4)
    return "$($ranks[$rankIndex])$($suits[$CardId % 4])"
}

function Get-TsGpuPossibleCards([object]$Response) {
    $maskValue = Get-TsGpuProperty $Response 'possible_cards' $null
    if ($null -eq $maskValue) { throw 'solver.cards.possible response has no possible_cards field.' }
    $mask = [uint64]$maskValue
    $cards = [System.Collections.Generic.List[int]]::new()
    for ($i = 0; $i -lt 52; $i++) {
        if (($mask -band ([uint64]1 -shl $i)) -ne 0) { $cards.Add($i) }
    }
    if ($cards.Count -eq 0) { throw 'solver.cards.possible returned an empty card set.' }
    return $cards.ToArray()
}

function Get-TsGpuChanceBoundaries([object]$Node) {
    $result = [System.Collections.Generic.List[object]]::new()
    function Visit-TsGpuNode([object]$Current, [int[]]$Path, [System.Collections.Generic.List[object]]$Sink) {
        if ($null -eq $Current) { return }
        if ([string](Get-TsGpuProperty $Current 'type' '') -eq 'chance') {
            $childrenProperty = $Current.PSObject.Properties['childrens']
            if ($null -ne $childrenProperty) {
                $children = $childrenProperty.Value
                $childCount = if ($children -is [System.Array]) { $children.Count } else { @($children.PSObject.Properties).Count }
                if ($childCount -ne 0) { throw 'current-street export unexpectedly crossed a chance boundary.' }
            }
            $Sink.Add([pscustomobject]@{ RelativeHistory = [int[]]@($Path) })
            return
        }
        $childrenProperty = $Current.PSObject.Properties['childrens']
        if ($null -eq $childrenProperty) { return }
        $children = $childrenProperty.Value
        if ($children -isnot [System.Array]) { return }
        for ($i = 0; $i -lt $children.Count; $i++) {
            Visit-TsGpuNode $children[$i] ([int[]]@($Path + $i)) $Sink
        }
    }
    Visit-TsGpuNode $Node ([int[]]@()) $result
    return $result.ToArray()
}

function Test-TsGpuStreetFragment([object]$Node, [int]$ExpectedRound) {
    $counts = [ordered]@{ action = 0; chance = 0; terminal = 0 }
    function Test-TsGpuNode([object]$Current, [int]$Round, [object]$Counter) {
        if ($null -eq $Current) { throw 'Native export contains a null node.' }
        $type = [string](Get-TsGpuProperty $Current 'type' '')
        if ($type -notin @('action', 'chance', 'terminal')) { throw "Unknown native node type: '$type'." }
        $Counter[$type] = [int]$Counter[$type] + 1
        $roundProperty = $Current.PSObject.Properties['betting round']
        if ($null -ne $roundProperty -and [int]$roundProperty.Value -ne $Round) {
            throw "Fragment contains betting round $($roundProperty.Value), expected $Round."
        }
        if ($type -eq 'action') {
            $strategy = Get-TsGpuProperty $Current 'strategy' $null
            if ($null -eq $strategy) { throw 'Native action node has no strategy.' }
            foreach ($field in @('card_strings', 'reach_probs', 'strategy_probs', 'action_evs', 'evs')) {
                if ($null -eq (Get-TsGpuProperty $strategy $field $null)) { throw "Native action strategy has no $field." }
            }
        }
        $childrenProperty = $Current.PSObject.Properties['childrens']
        if ($null -eq $childrenProperty) { return }
        $children = $childrenProperty.Value
        if ($children -is [System.Array]) {
            foreach ($child in $children) { Test-TsGpuNode $child $Round $Counter }
        } elseif ($null -ne $children) {
            foreach ($property in $children.PSObject.Properties) { Test-TsGpuNode $property.Value $Round $Counter }
        }
    }
    Test-TsGpuNode $Node $ExpectedRound $counts
    return [pscustomobject]$counts
}

function Add-TsGpuZipText([IO.Compression.ZipArchive]$Archive, [string]$EntryName, [string]$Text) {
    $entry = $Archive.CreateEntry($EntryName, [IO.Compression.CompressionLevel]::Optimal)
    $stream = $entry.Open()
    $utf8 = [Text.UTF8Encoding]::new($false)
    $writer = [IO.StreamWriter]::new($stream, $utf8, 65536, $true)
    try { $writer.Write($Text) } finally { $writer.Dispose(); $stream.Dispose() }
}

function Export-TsGpuFullTree {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][Net.WebSockets.ClientWebSocket]$Socket,
        [Parameter(Mandatory = $true)][System.Collections.Generic.List[object]]$Transcript,
        [Parameter(Mandatory = $true)][string]$OutputDirectory,
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string]$SolverPath,
        [Parameter(Mandatory = $true)][string]$Board,
        [Parameter(Mandatory = $true)][int[]]$BoardIds,
        [Parameter(Mandatory = $true)][int]$MaxIterations,
        [Parameter(Mandatory = $true)][double]$TargetExploitability,
        [Parameter(Mandatory = $true)][object]$FinalStatus,
        [Parameter(Mandatory = $true)][string]$RunnerVersion,
        [Parameter(Mandatory = $true)][string]$RunnerCommit,
        [Parameter(Mandatory = $true)][string]$RunnerSourcePath,
        [Parameter(Mandatory = $true)][string]$ExporterSourcePath,
        [int]$ExportMaxNodes = 100000,
        [int]$DiagnosticFragmentLimit = 0
    )

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $started = [DateTime]::UtcNow
    $workingPath = Join-Path $OutputDirectory 'full-tree.working.zip'
    $completePath = Join-Path $OutputDirectory 'full-tree.tsgpu.zip'
    $partialPath = Join-Path $OutputDirectory 'full-tree.diagnostic-partial.zip'
    foreach ($path in @($workingPath, $completePath, $partialPath)) {
        if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite existing full-tree archive: $path" }
    }

    $fileStream = [IO.FileStream]::new($workingPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $archive = [IO.Compression.ZipArchive]::new($fileStream, [IO.Compression.ZipArchiveMode]::Create, $false)
    $indexLines = [System.Collections.Generic.List[string]]::new()
    $pending = [System.Collections.Stack]::new()
    $pending.Push([pscustomobject]@{ History = [int[]]@(); Street = 1 })
    $seen = @{}
    $fragmentCounts = [ordered]@{ flop = 0; turn = 0; river = 0 }
    $nodeCounts = [ordered]@{ action = 0; chance = 0; terminal = 0 }
    $chanceBoundaryCount = 0
    $chanceEdgeCount = 0
    $fragmentNumber = 0
    $completed = $false

    try {
        while ($pending.Count -gt 0) {
            if ($DiagnosticFragmentLimit -gt 0 -and $fragmentNumber -ge $DiagnosticFragmentLimit) { break }
            $work = $pending.Pop()
            $history = [int[]]@($work.History)
            $street = [int]$work.Street
            $historyKey = Get-TsGpuHistoryKey $history
            if ($seen.ContainsKey($historyKey)) { throw "Duplicate fragment history discovered: $historyKey" }
            $seen[$historyKey] = $true

            Invoke-Bridge $Socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $history }) 10000 $Transcript | Out-Null
            $export = Invoke-Bridge $Socket 'solver.export.currentStreet' '/api/export/current-street' 'POST' ([ordered]@{
                history = $history
                max_nodes = $ExportMaxNodes
            }) 120000 $Transcript
            $payload = Get-TsGpuProperty $export 'payload' $export
            $counts = Test-TsGpuStreetFragment $payload $street
            foreach ($type in @('action', 'chance', 'terminal')) { $nodeCounts[$type] = [int]$nodeCounts[$type] + [int]$counts.$type }

            $nativeJson = ConvertTo-TsGpuCompactJson $payload
            $nativeBytes = [Text.Encoding]::UTF8.GetBytes($nativeJson)
            $fragmentNumber++
            $streetName = @('', 'flop', 'turn', 'river')[$street]
            $fragmentCounts[$streetName] = [int]$fragmentCounts[$streetName] + 1
            $entryName = 'fragments/{0}/{1:D8}.json' -f $streetName, $fragmentNumber
            Add-TsGpuZipText $archive $entryName $nativeJson

            $boundaryRecords = [System.Collections.Generic.List[object]]::new()
            $boundaries = @(Get-TsGpuChanceBoundaries $payload)
            foreach ($boundary in $boundaries) {
                if ($street -ge 3) { throw 'River fragment unexpectedly contains a chance boundary.' }
                $chanceHistory = [int[]]@($history + @($boundary.RelativeHistory))
                Invoke-Bridge $Socket 'solver.history.apply' '/api/apply-history' 'POST' ([ordered]@{ history = $chanceHistory }) 10000 $Transcript | Out-Null
                $possible = Invoke-Bridge $Socket 'solver.cards.possible' '/api/possible-cards' 'GET' $null 10000 $Transcript
                $cards = [int[]]@(Get-TsGpuPossibleCards $possible)
                $children = [System.Collections.Generic.List[object]]::new()
                for ($i = $cards.Count - 1; $i -ge 0; $i--) {
                    $card = [int]$cards[$i]
                    $childHistory = [int[]]@($chanceHistory + $card)
                    $pending.Push([pscustomobject]@{ History = $childHistory; Street = $street + 1 })
                }
                foreach ($card in $cards) {
                    $childHistory = [int[]]@($chanceHistory + [int]$card)
                    $children.Add([ordered]@{
                        card_id = [int]$card
                        card = Convert-TsGpuCardIdToText ([int]$card)
                        history = $childHistory
                        history_key = Get-TsGpuHistoryKey $childHistory
                    })
                }
                $chanceBoundaryCount++
                $chanceEdgeCount += $cards.Count
                $boundaryRecords.Add([ordered]@{
                    relative_history = [int[]]@($boundary.RelativeHistory)
                    history = $chanceHistory
                    legal_cards = $children
                })
            }

            $record = [ordered]@{
                fragment_id = $fragmentNumber
                entry = $entryName
                street = $streetName
                betting_round = $street
                history = $history
                history_key = $historyKey
                native_sha256 = Get-TsGpuSha256Bytes $nativeBytes
                native_bytes = $nativeBytes.Length
                native_node_count = Get-TsGpuProperty $export 'node_count' $null
                validated_nodes = $counts
                chance_boundaries = $boundaryRecords
            }
            $indexLines.Add((ConvertTo-TsGpuCompactJson $record))
            if ($fragmentNumber -eq 1 -or $fragmentNumber % 100 -eq 0) {
                Write-Host "Full-tree export: $fragmentNumber fragments; pending=$($pending.Count); street=$streetName"
            }
        }
        $completed = $pending.Count -eq 0

        $configText = [IO.File]::ReadAllText($ConfigPath, [Text.Encoding]::UTF8)
        Add-TsGpuZipText $archive 'metadata/config.json' $configText
        Add-TsGpuZipText $archive 'metadata/tsgpu-worker.ps1' ([IO.File]::ReadAllText($RunnerSourcePath, [Text.Encoding]::UTF8))
        Add-TsGpuZipText $archive 'metadata/FullTree-Export.ps1' ([IO.File]::ReadAllText($ExporterSourcePath, [Text.Encoding]::UTF8))
        Add-TsGpuZipText $archive 'index.jsonl' ($indexLines -join "`n")
        $manifest = [ordered]@{
            schema_version = 1
            format = 'texassolvergpu-full-tree-fragments'
            complete = $completed
            native_format = 'solver.export.currentStreet payload'
            created_at_utc = [DateTime]::UtcNow.ToString('o')
            board = $Board
            board_ids = $BoardIds
            solver_exe = $SolverPath
            solver_sha256 = (Get-FileHash -LiteralPath $SolverPath -Algorithm SHA256).Hash.ToLowerInvariant()
            runner_version = $RunnerVersion
            runner_commit = $RunnerCommit
            runner_source_sha256 = (Get-FileHash -LiteralPath $RunnerSourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
            exporter_source_sha256 = (Get-FileHash -LiteralPath $ExporterSourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
            config_sha256 = (Get-FileHash -LiteralPath $ConfigPath -Algorithm SHA256).Hash.ToLowerInvariant()
            max_iterations = $MaxIterations
            target_exploitability = $TargetExploitability
            final_status = $FinalStatus
            export_method = 'solver.export.currentStreet'
            export_endpoint = 'POST /api/export/current-street'
            navigation_method = 'solver.history.apply'
            legal_cards_method = 'solver.cards.possible'
            fragment_count = $fragmentNumber
            pending_fragment_count = $pending.Count
            fragments_by_street = $fragmentCounts
            validated_nodes = $nodeCounts
            chance_boundary_count = $chanceBoundaryCount
            chance_edge_count = $chanceEdgeCount
            strategy_fields = @('card_strings', 'reach_probs', 'strategy_probs', 'action_evs', 'evs')
            elapsed_ms = [int64]([DateTime]::UtcNow - $started).TotalMilliseconds
        }
        Add-TsGpuZipText $archive 'manifest.json' (ConvertTo-TsGpuCompactJson $manifest)
    } finally {
        $archive.Dispose()
        $fileStream.Dispose()
    }

    $finalPath = if ($completed) { $completePath } else { $partialPath }
    [IO.File]::Move($workingPath, $finalPath)
    $result = [ordered]@{
        complete = $completed
        archive = [IO.Path]::GetFileName($finalPath)
        archive_path = $finalPath
        archive_sha256 = (Get-FileHash -LiteralPath $finalPath -Algorithm SHA256).Hash.ToLowerInvariant()
        archive_bytes = (Get-Item -LiteralPath $finalPath).Length
        fragment_count = $fragmentNumber
        pending_fragment_count = $pending.Count
        fragments_by_street = $fragmentCounts
        validated_nodes = $nodeCounts
        chance_boundary_count = $chanceBoundaryCount
        chance_edge_count = $chanceEdgeCount
        export_method = 'solver.export.currentStreet'
        export_endpoint = 'POST /api/export/current-street'
        elapsed_ms = [int64]([DateTime]::UtcNow - $started).TotalMilliseconds
    }
    return [pscustomobject]$result
}

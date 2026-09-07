Set-StrictMode -Version Latest

function Read-TexasSolverRangeMap {
    param([Parameter(Mandatory = $true)][string]$Path)

    $raw = (Get-Content -LiteralPath $Path -Raw -Encoding UTF8).Trim()
    if (-not $raw) { throw "Range file is empty: $Path" }

    $map = @{}
    foreach ($entry in ($raw -split ',')) {
        $item = $entry.Trim()
        if (-not $item) { continue }
        $parts = @($item -split ':')
        if ($parts.Count -ne 2) { throw "Invalid range token '$item' in $Path" }
        $key = $parts[0].Trim()
        if ($key -notmatch '^(?:[2-9TJQKA]{2}|[2-9TJQKA]{2}[so])$') {
            throw "Invalid starting-hand key '$key' in $Path"
        }
        if ($map.ContainsKey($key)) { throw "Duplicate starting-hand key '$key' in $Path" }
        $value = [double]::Parse($parts[1].Trim(), [Globalization.CultureInfo]::InvariantCulture)
        if ($value -lt 0.0 -or $value -gt 1.0) { throw "Weight for '$key' must be between 0 and 1; got $value" }
        $map[$key] = $value
    }
    return $map
}

function Get-TexasSolverStartingHandKey {
    param(
        [Parameter(Mandatory = $true)][int]$CardA,
        [Parameter(Mandatory = $true)][int]$CardB
    )

    if ($CardA -lt 0 -or $CardA -gt 51 -or $CardB -lt 0 -or $CardB -gt 51 -or $CardA -eq $CardB) {
        throw "Invalid card ids: $CardA, $CardB"
    }

    $ranks = '23456789TJQKA'
    $rankA = [int][Math]::Floor([double]$CardA / 4.0)
    $rankB = [int][Math]::Floor([double]$CardB / 4.0)
    $suitA = $CardA % 4
    $suitB = $CardB % 4

    if ($rankA -eq $rankB) {
        $r = $ranks.Substring($rankA, 1)
        return "$r$r"
    }

    $high = [Math]::Max($rankA, $rankB)
    $low = [Math]::Min($rankA, $rankB)
    $suffix = if ($suitA -eq $suitB) { 's' } else { 'o' }
    return ($ranks.Substring([int]$high, 1) + $ranks.Substring([int]$low, 1) + $suffix)
}

function Convert-TexasSolverRangeTo1326 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $map = Read-TexasSolverRangeMap -Path $Path
    $values = [System.Collections.Generic.List[double]]::new()
    for ($a = 0; $a -lt 51; $a++) {
        for ($b = $a + 1; $b -lt 52; $b++) {
            $key = Get-TexasSolverStartingHandKey -CardA $a -CardB $b
            $weight = if ($map.ContainsKey($key)) { [double]$map[$key] } else { 0.0 }
            $values.Add($weight)
        }
    }
    if ($values.Count -ne 1326) { throw "Expanded range must contain 1326 combos; got $($values.Count)." }
    return $values.ToArray()
}

function Get-TexasSolverWeightedComboCount {
    param([Parameter(Mandatory = $true)][string]$Path)
    $values = @(Convert-TexasSolverRangeTo1326 -Path $Path)
    return [double](($values | Measure-Object -Sum).Sum)
}

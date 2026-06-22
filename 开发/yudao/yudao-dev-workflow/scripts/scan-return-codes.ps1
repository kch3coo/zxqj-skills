param(
    [Parameter(Mandatory = $true)]
    [string]$Root,

    [string]$Prefix,

    [string]$IncludePath
)

$ErrorActionPreference = "Stop"

function Normalize-Code {
    param([string]$Code)
    return ($Code -replace "_", "")
}

function Format-Code {
    param([string]$Digits)
    if ($Digits.Length -le 1) {
        return $Digits
    }
    $groups = @()
    $remaining = $Digits
    while ($remaining.Length -gt 3) {
        $groups = ,$remaining.Substring($remaining.Length - 3) + $groups
        $remaining = $remaining.Substring(0, $remaining.Length - 3)
    }
    $groups = ,$remaining + $groups
    return ($groups -join "_")
}

function Resolve-Path-Safely {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Path not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-Relative-Path {
    param(
        [string]$BasePath,
        [string]$TargetPath
    )
    $base = $BasePath.TrimEnd("\", "/")
    if ($TargetPath.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $TargetPath.Substring($base.Length).TrimStart("\", "/")
    }
    return $TargetPath
}

$resolvedRoot = Resolve-Path-Safely -Path $Root
$normalizedPrefix = $null
if ($Prefix -and $Prefix.Trim().Length -gt 0) {
    $normalizedPrefix = Normalize-Code -Code $Prefix.Trim()
}

$files = Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File -Filter "*.java"
if ($IncludePath -and $IncludePath.Trim().Length -gt 0) {
    $include = $IncludePath.Trim().Replace("/", "\")
    $files = $files | Where-Object { $_.FullName.Replace("/", "\").Contains($include) }
}

$pattern = 'new\s+ReturnCode\s*\(\s*([0-9][0-9_]*)'
$records = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    $lineNo = 0
    foreach ($line in Get-Content -Encoding UTF8 -LiteralPath $file.FullName) {
        $lineNo++
        $matches = [regex]::Matches($line, $pattern)
        foreach ($match in $matches) {
            $rawCode = $match.Groups[1].Value
            $digits = Normalize-Code -Code $rawCode
            if ($normalizedPrefix -and -not $digits.StartsWith($normalizedPrefix)) {
                continue
            }

            $name = ""
            $nameMatch = [regex]::Match($line, 'ReturnCode\s+([A-Z0-9_]+)\s*=')
            if ($nameMatch.Success) {
                $name = $nameMatch.Groups[1].Value
            }

            $relativePath = Get-Relative-Path -BasePath $resolvedRoot -TargetPath $file.FullName
            $records.Add([PSCustomObject]@{
                Code = $digits
                DisplayCode = Format-Code -Digits $digits
                Name = $name
                File = $relativePath
                Line = $lineNo
                Text = $line.Trim()
            })
        }
    }
}

Write-Output "ReturnCode scan root: $Root"
if ($IncludePath) {
    Write-Output "Include path filter: $IncludePath"
}
if ($Prefix) {
    Write-Output "Prefix: $Prefix"
}
Write-Output "Matched codes: $($records.Count)"
Write-Output ""

if ($records.Count -eq 0) {
    Write-Output "No ReturnCode values found."
    exit 0
}

$duplicates = $records | Group-Object Code | Where-Object { $_.Count -gt 1 } | Sort-Object Name
if ($duplicates.Count -eq 0) {
    Write-Output "No duplicate ReturnCode values found."
} else {
    Write-Output "Duplicate ReturnCode values:"
    foreach ($group in $duplicates) {
        Write-Output "$((Format-Code -Digits $group.Name))"
        foreach ($item in ($group.Group | Sort-Object File, Line)) {
            $label = if ($item.Name) { " $($item.Name)" } else { "" }
            Write-Output "  $($item.File):$($item.Line)$label"
        }
    }
}

if ($normalizedPrefix) {
    $used = @{}
    foreach ($record in $records) {
        $used[$record.Code] = $true
    }

    $width = 3
    $maxSuffix = -1
    foreach ($record in $records) {
        if ($record.Code.Length -gt $normalizedPrefix.Length) {
            $suffix = $record.Code.Substring($normalizedPrefix.Length)
            if ($suffix -match '^\d+$') {
                $width = [Math]::Max($width, $suffix.Length)
                $maxSuffix = [Math]::Max($maxSuffix, [int]$suffix)
            }
        }
    }

    $candidate = if ($maxSuffix -lt 0) { 0 } else { $maxSuffix + 1 }
    while ($true) {
        $candidateCode = $normalizedPrefix + $candidate.ToString(("D" + $width))
        if (-not $used.ContainsKey($candidateCode)) {
            Write-Output ""
            Write-Output "Next available in $Prefix`: $((Format-Code -Digits $candidateCode))"
            break
        }
        $candidate++
    }
}

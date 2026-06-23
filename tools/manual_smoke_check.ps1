# Verify interactive manual smoke evidence before release.
# This script reads MANUAL_SMOKE_VALIDATION.md only; it does not launch apps.

param(
    [string]$Path = "MANUAL_SMOKE_VALIDATION.md",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$requiredChecks = @(
    '`/control` opens on `127.0.0.1:7778`',
    '`/control` status display updates',
    '`/control` Preview Voice plays audio',
    '`/control` Speak text works',
    '`/control` Speak + Save WAV creates WAV',
    '`/control` Stop playback works',
    '`/control` history toggle and Clear History work',
    'Tk desktop opens on supported non-macOS target or `READOUT_FORCE_TK=1`',
    'Desktop engine, voice, and speed controls persist through backend config',
    'Desktop Preview Voice plays audio',
    'Desktop Speak, Save WAV, and Stop work',
    'Extension origin added to `allowed_origins`',
    'Popup shows READY when server is up',
    'Popup shows OFFLINE or next action when server is down',
    'Popup Preview Voice works',
    'Context menu Read aloud works on selected page text',
    'Extension Stop playback works'
)

$summaryItems = @(
    'Source `/control` manual smoke',
    'Tk desktop manual smoke',
    'Chrome extension manual smoke'
)

function Convert-MarkdownTableRow {
    param([string]$Line)

    if ($Line -notmatch "^\|") {
        return $null
    }

    $columns = $Line.Trim().Trim("|") -split "\|" | ForEach-Object { $_.Trim() }
    if ($columns.Count -lt 3) {
        return $null
    }

    if ($columns[0] -in @("---", "Check", "Item")) {
        return $null
    }

    return $columns
}

function Test-FilledEvidence {
    param([string]$Text)

    $cleaned = $Text.Trim()
    return $cleaned -ne "" -and $cleaned -notmatch "^(TBD|Pending)$"
}

function Test-PassingResult {
    param(
        [string]$Result,
        [string]$Evidence
    )

    $cleaned = $Result.Trim()
    if ($cleaned -match "^(PASS|PASSED|OK|DONE|COMPLETE|COMPLETED)$") {
        return Test-FilledEvidence -Text $Evidence
    }

    if ($cleaned -match "^(ACCEPTED GAP|ACCEPTED RISK)$") {
        return Test-FilledEvidence -Text $Evidence
    }

    return $false
}

function Add-Result {
    param(
        [System.Collections.Generic.List[object]]$Results,
        [string]$Check,
        [string]$Result,
        [string]$Detail
    )

    $Results.Add([pscustomobject]@{
        Check = $Check
        Result = $Result
        Detail = $Detail
    })
}

if (-not (Test-Path $Path)) {
    if (-not $Quiet) {
        Write-Host "Manual smoke validation file not found: $Path"
    }
    exit 1
}

$rows = @{}
foreach ($line in Get-Content -Path $Path) {
    $columns = Convert-MarkdownTableRow -Line $line
    if (-not $columns) {
        continue
    }

    $rows[$columns[0]] = [pscustomobject]@{
        Result = $columns[1]
        Evidence = $columns[2]
    }
}

$results = New-Object System.Collections.Generic.List[object]

foreach ($check in $requiredChecks) {
    if (-not $rows.ContainsKey($check)) {
        Add-Result -Results $results -Check $check -Result "FAIL" -Detail "Missing worksheet row."
        continue
    }

    $row = $rows[$check]
    if (Test-PassingResult -Result $row.Result -Evidence $row.Evidence) {
        Add-Result -Results $results -Check $check -Result "PASS" -Detail $row.Result
    } else {
        Add-Result -Results $results -Check $check -Result "FAIL" -Detail "Result must be PASS/PASSED/OK/DONE/COMPLETE with evidence, or ACCEPTED GAP with evidence. Current: $($row.Result)"
    }
}

foreach ($item in $summaryItems) {
    if (-not $rows.ContainsKey($item)) {
        Add-Result -Results $results -Check $item -Result "FAIL" -Detail "Missing manual smoke summary row."
        continue
    }

    $row = $rows[$item]
    if (Test-PassingResult -Result $row.Result -Evidence $row.Evidence) {
        Add-Result -Results $results -Check $item -Result "PASS" -Detail $row.Result
    } else {
        Add-Result -Results $results -Check $item -Result "FAIL" -Detail "Summary status is not release-ready. Current: $($row.Result)"
    }
}

if (-not $Quiet) {
    Write-Host "| Check | Result | Detail |"
    Write-Host "|---|---|---|"
    foreach ($row in $results) {
        Write-Host "| $($row.Check) | $($row.Result) | $($row.Detail) |"
    }
}

$hasFailure = $false
foreach ($row in $results) {
    if ([string]$row.Result -eq "FAIL") {
        $hasFailure = $true
        break
    }
}

if ($hasFailure) {
    exit 1
}

exit 0

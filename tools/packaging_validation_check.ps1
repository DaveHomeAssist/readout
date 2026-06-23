# Verify target packaging validation evidence before release.
# This script reads PACKAGING_VALIDATION.md only; it does not build packages.

param(
    [string]$Path = "PACKAGING_VALIDATION.md",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$requiredChecks = @(
    '`ARCHITECT_SIGNOFF.md` reviewed',
    '`.\tools\release_preflight.ps1` or target equivalent run',
    'Python 3.10-3.12 confirmed',
    '`espeak-ng` confirmed on PATH',
    'Full test suite run',
    '`./build_mac.sh` completed',
    '`dist/ReadOut.app` exists',
    '`tools/mac_package_smoke.sh` passed',
    'Menu-bar/tray icon visible',
    'Tray `Open Control Panel` opens `/control`',
    'macOS preview/speak/stop lifecycle verified',
    'App quits cleanly',
    '`.\build_windows.ps1` completed',
    '`dist\ReadOut\ReadOut.exe` exists',
    '`tools\windows_package_smoke.ps1` passed',
    'Server starts on `127.0.0.1:7778`',
    '`/control` opens and displays controls',
    'Windows preview/speak/stop lifecycle verified',
    'App process stops cleanly'
)

$summaryItems = @(
    'P3-A1 macOS packaging',
    'P3-A2 Windows packaging',
    'P3-A4 release checklist accepted'
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

    if ($columns[0] -in @("---", "Check", "Item", "Gap")) {
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
        Write-Host "Packaging validation file not found: $Path"
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
        Add-Result -Results $results -Check $item -Result "FAIL" -Detail "Missing release evidence summary row."
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

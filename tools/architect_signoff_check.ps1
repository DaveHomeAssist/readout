# Verify required Architect sign-off rows before release.
# This script reads ARCHITECT_SIGNOFF.md only; it does not edit files.

param(
    [string]$Path = "ARCHITECT_SIGNOFF.md",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$requiredIds = @(
    "P0-A4",
    "P1-A2",
    "P1-A4",
    "P1-A5",
    "P2-A1",
    "P2-A4",
    "P3-A4"
)

function Test-CheckboxChecked {
    param([string]$Text)

    return $Text.Trim() -match "^\[[xX]\]$"
}

function Add-Result {
    param(
        [System.Collections.Generic.List[object]]$Results,
        [string]$Id,
        [string]$Result,
        [string]$Detail
    )

    $Results.Add([pscustomobject]@{
        ID = $Id
        Result = $Result
        Detail = $Detail
    })
}

if (-not (Test-Path $Path)) {
    if (-not $Quiet) {
        Write-Host "Architect sign-off file not found: $Path"
    }
    exit 1
}

$rowsById = @{}
foreach ($line in Get-Content -Path $Path) {
    if ($line -notmatch "^\|\s*P\d-A\d\s*\|") {
        continue
    }

    $columns = $line.Trim().Trim("|") -split "\|" | ForEach-Object { $_.Trim() }
    if ($columns.Count -lt 6) {
        continue
    }

    $rowsById[$columns[0]] = [pscustomobject]@{
        Decision = $columns[1]
        Accept = $columns[3]
        Revise = $columns[4]
    }
}

$results = New-Object System.Collections.Generic.List[object]

foreach ($id in $requiredIds) {
    if (-not $rowsById.ContainsKey($id)) {
        Add-Result -Results $results -Id $id -Result "FAIL" -Detail "Missing required sign-off row."
        continue
    }

    $row = $rowsById[$id]
    $accepted = Test-CheckboxChecked -Text $row.Accept
    $revise = Test-CheckboxChecked -Text $row.Revise

    if ($accepted -and -not $revise) {
        Add-Result -Results $results -Id $id -Result "PASS" -Detail "Accepted."
    } elseif ($accepted -and $revise) {
        Add-Result -Results $results -Id $id -Result "FAIL" -Detail "Both Accept and Revise are checked."
    } elseif ($revise) {
        Add-Result -Results $results -Id $id -Result "FAIL" -Detail "Revise is checked; Architect changes are required."
    } else {
        Add-Result -Results $results -Id $id -Result "FAIL" -Detail "Accept is not checked."
    }
}

if (-not $Quiet) {
    Write-Host "| ID | Result | Detail |"
    Write-Host "|---|---|---|"
    foreach ($row in $results) {
        Write-Host "| $($row.ID) | $($row.Result) | $($row.Detail) |"
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

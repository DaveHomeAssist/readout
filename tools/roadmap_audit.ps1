# Summarize ReadOut roadmap completion gates without mutating the worktree.
# This script does not fetch, merge, build packages, launch GUI apps, or edit files.

param(
    [string]$Upstream = "origin/main"
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$script:GitSafeDirectory = ((Resolve-Path ".").Path -replace "\\", "/")

function Add-Result {
    param(
        [string]$Area,
        [string]$Result,
        [string]$Detail,
        [string]$NextAction
    )

    $results.Add([pscustomobject]@{
        Area = $Area
        Result = $Result
        Detail = $Detail
        NextAction = $NextAction
    })
}

function Invoke-QuietScript {
    param(
        [string]$Path,
        [string[]]$Args = @()
    )

    try {
        & $Path @Args -Quiet *> $null
        return $LASTEXITCODE
    } catch {
        return 1
    }
}

function Test-CommandAvailable {
    param([string]$Exe)

    if ($Exe -match "[\\/]") {
        return Test-Path $Exe
    }

    return [bool](Get-Command $Exe -ErrorAction SilentlyContinue)
}

function Test-SupportedPython {
    param(
        [string]$Exe,
        [string[]]$BaseArgs = @()
    )

    $check = "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 13) else 1)"
    try {
        $argv = @($BaseArgs + @("-c", $check))
        & $Exe @argv *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

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

function Test-ReleaseEvidencePass {
    param([string]$Result, [string]$Evidence)

    return (
        $Result.Trim() -match "^(PASS|PASSED|OK|DONE|COMPLETE|COMPLETED)$" -and
        $Evidence.Trim() -ne "" -and
        $Evidence.Trim() -notmatch "^(TBD|Pending)$"
    )
}

function Get-PackagingEvidence {
    param([string]$Check)

    if (-not (Test-Path "PACKAGING_VALIDATION.md")) {
        return $null
    }

    foreach ($line in Get-Content -Path "PACKAGING_VALIDATION.md") {
        $columns = Convert-MarkdownTableRow -Line $line
        if (-not $columns) {
            continue
        }

        if ($columns[0] -eq $Check -and (Test-ReleaseEvidencePass -Result $columns[1] -Evidence $columns[2])) {
            return $columns[2]
        }
    }

    return $null
}

function Limit-Detail {
    param([string]$Text, [int]$Length = 160)

    $cleaned = ($Text -replace "\|", "/" -replace "\s+", " ").Trim()
    if ($cleaned.Length -le $Length) {
        return $cleaned
    }

    return $cleaned.Substring(0, $Length) + "..."
}

function Resolve-SupportedPythonLabel {
    $candidates = @(
        @{ Label = "existing .venv"; Exe = ".\.venv\Scripts\python.exe"; Args = @() },
        @{ Label = "Python Launcher 3.12"; Exe = "py"; Args = @("-3.12") },
        @{ Label = "Python Launcher 3.11"; Exe = "py"; Args = @("-3.11") },
        @{ Label = "Python Launcher 3.10"; Exe = "py"; Args = @("-3.10") },
        @{ Label = "python on PATH"; Exe = "python"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Test-CommandAvailable $candidate.Exe)) {
            continue
        }

        if (Test-SupportedPython -Exe $candidate.Exe -BaseArgs $candidate.Args) {
            return $candidate.Label
        }
    }

    return $null
}

function Test-RoadmapRows {
    $requiredIds = @(
        "P0-A1", "P0-A2", "P0-A3", "P0-A4",
        "P1-A1", "P1-A2", "P1-A3", "P1-A4", "P1-A5",
        "P2-A1", "P2-A2", "P2-A3", "P2-A4",
        "P3-A1", "P3-A2", "P3-A3", "P3-A4"
    )

    if (-not (Test-Path "ROADMAP_STATUS.md")) {
        Add-Result -Area "Roadmap status artifact" -Result "FAIL" -Detail "ROADMAP_STATUS.md missing." -NextAction "Restore the roadmap status artifact."
        return
    }

    $text = Get-Content -Path "ROADMAP_STATUS.md" -Raw
    $missing = @($requiredIds | Where-Object { $text -notmatch "\| $($_) \|" })
    if ($missing.Count -eq 0) {
        Add-Result -Area "Roadmap item coverage" -Result "PASS" -Detail "All roadmap IDs are represented." -NextAction "Keep status artifact current."
    } else {
        Add-Result -Area "Roadmap item coverage" -Result "FAIL" -Detail ("Missing IDs: " + ($missing -join ", ")) -NextAction "Update ROADMAP_STATUS.md."
    }
}

function Invoke-GitText {
    param([string[]]$GitArgs)

    $output = & git -c "safe.directory=$script:GitSafeDirectory" @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ($output -join "`n")
    }
    return $output
}

function Test-UpstreamCurrency {
    try {
        try {
            Invoke-GitText -GitArgs @("rev-parse", "--verify", $Upstream) *> $null
        } catch {
            Add-Result -Area "Upstream graph" -Result "FAIL" -Detail "$Upstream is not available locally." -NextAction "Refresh or configure the upstream ref."
            return
        }

        $counts = Invoke-GitText -GitArgs @("rev-list", "--left-right", "--count", "HEAD...$Upstream")
        if (-not $counts) {
            Add-Result -Area "Upstream graph" -Result "FAIL" -Detail "Could not compare HEAD with $Upstream." -NextAction "Run git status/log diagnostics."
            return
        }

        $parts = ($counts -split "\s+") | Where-Object { $_ -ne "" }
        $ahead = [int]$parts[0]
        $behind = [int]$parts[1]
        if ($behind -gt 0) {
            Add-Result -Area "Upstream graph" -Result "FAIL" -Detail "ahead=$ahead; behind=$behind vs $Upstream" -NextAction "Review UPSTREAM_RECONCILIATION.md before accepting or merging remote delta."
        } else {
            Add-Result -Area "Upstream graph" -Result "PASS" -Detail "ahead=$ahead; behind=$behind vs $Upstream" -NextAction "No upstream graph blocker."
        }
    } catch {
        Add-Result -Area "Upstream graph" -Result "FAIL" -Detail $_.Exception.Message -NextAction "Run git status/log diagnostics."
    }
}

Write-Host "ReadOut roadmap audit"
Write-Host "Working directory: $(Get-Location)"

Test-RoadmapRows
Test-UpstreamCurrency

$pythonEvidence = Get-PackagingEvidence -Check "Python 3.10-3.12 confirmed"
$pythonLabel = Resolve-SupportedPythonLabel
if ($pythonLabel) {
    Add-Result -Area "Python 3.10-3.12" -Result "PASS" -Detail "Found via $pythonLabel." -NextAction "Use this runtime for release packaging."
} elseif ($pythonEvidence) {
    Add-Result -Area "Python 3.10-3.12" -Result "PASS" -Detail ("Hosted/target evidence recorded: " + (Limit-Detail -Text $pythonEvidence)) -NextAction "No local install needed unless building packages on this host."
} else {
    Add-Result -Area "Python 3.10-3.12" -Result "FAIL" -Detail "No supported Python runtime found." -NextAction "Install Python 3.12, 3.11, or 3.10."
}

$espeakEvidence = Get-PackagingEvidence -Check '`espeak-ng` confirmed on PATH'
if (Get-Command espeak-ng -ErrorAction SilentlyContinue) {
    Add-Result -Area "espeak-ng" -Result "PASS" -Detail "Found on PATH." -NextAction "Keep available for package validation."
} elseif ($espeakEvidence) {
    Add-Result -Area "espeak-ng" -Result "PASS" -Detail ("Hosted/target evidence recorded: " + (Limit-Detail -Text $espeakEvidence)) -NextAction "No local install needed unless building packages on this host."
} else {
    Add-Result -Area "espeak-ng" -Result "FAIL" -Detail "Not found on PATH." -NextAction "Install espeak-ng and verify espeak-ng --version."
}

$signoffExit = Invoke-QuietScript -Path ".\tools\architect_signoff_check.ps1"
Add-Result -Area "Architect sign-off" -Result ($(if ($signoffExit -eq 0) { "PASS" } else { "FAIL" })) -Detail "architect_signoff_check.ps1 exit=$signoffExit" -NextAction "Complete ARCHITECT_SIGNOFF.md and rerun the checker."

$packagingExit = Invoke-QuietScript -Path ".\tools\packaging_validation_check.ps1"
Add-Result -Area "Packaging validation" -Result ($(if ($packagingExit -eq 0) { "PASS" } else { "FAIL" })) -Detail "packaging_validation_check.ps1 exit=$packagingExit" -NextAction "Fill PACKAGING_VALIDATION.md on macOS and Windows targets."

$manualExit = Invoke-QuietScript -Path ".\tools\manual_smoke_check.ps1"
Add-Result -Area "Manual smoke validation" -Result ($(if ($manualExit -eq 0) { "PASS" } else { "FAIL" })) -Detail "manual_smoke_check.ps1 exit=$manualExit" -NextAction "Fill MANUAL_SMOKE_VALIDATION.md on the intended release machine."

Write-Host ""
Write-Host "| Area | Result | Detail | Next Action |"
Write-Host "|---|---|---|---|"
foreach ($row in $results) {
    Write-Host "| $($row.Area) | $($row.Result) | $($row.Detail) | $($row.NextAction) |"
}

$failedRows = @($results | Where-Object { $_.Result -eq "FAIL" })
if ($failedRows.Count -gt 0) {
    exit 1
}

exit 0

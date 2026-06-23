# Print a local-only upstream reconciliation report for ReadOut.
# The script does not fetch, merge, rebase, reset, checkout, or edit files.

param(
    [string]$Upstream = "origin/main"
)

$ErrorActionPreference = "Stop"

$script:GitSafeDirectory = ((Resolve-Path ".").Path -replace "\\", "/")

function Invoke-GitText {
    param([string[]]$GitArgs)

    $output = & git -c "safe.directory=$script:GitSafeDirectory" @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ($output -join "`n")
    }
    return $output
}

function Write-TableRow {
    param(
        [string]$Check,
        [string]$Result,
        [string]$Detail
    )

    Write-Host "| $Check | $Result | $Detail |"
}

$inside = Invoke-GitText -GitArgs @("rev-parse", "--is-inside-work-tree")
if (($inside | Select-Object -First 1) -ne "true") {
    throw "Not inside a Git worktree."
}

Invoke-GitText -GitArgs @("rev-parse", "--verify", $Upstream) *> $null

$counts = Invoke-GitText -GitArgs @("rev-list", "--left-right", "--count", "HEAD...$Upstream")
$parts = (($counts | Select-Object -First 1) -split "\s+") | Where-Object { $_ -ne "" }
$ahead = [int]$parts[0]
$behind = [int]$parts[1]

Write-Host "ReadOut upstream reconciliation"
Write-Host "Upstream: $Upstream"
Write-Host ""
Write-Host "| Check | Result | Detail |"
Write-Host "|---|---|---|"
Write-TableRow -Check "Graph" -Result ($(if ($behind -eq 0) { "PASS" } else { "REVIEW" })) -Detail "ahead=$ahead; behind=$behind"

$status = Invoke-GitText -GitArgs @("status", "--short")
$dirtyCount = @($status | Where-Object { $_ }).Count
Write-TableRow -Check "Worktree" -Result ($(if ($dirtyCount -eq 0) { "PASS" } else { "REVIEW" })) -Detail "$dirtyCount changed/untracked path(s)"

$changedPaths = @(Invoke-GitText -GitArgs @("diff", "--name-only", "HEAD...$Upstream") | Where-Object { $_ })
$runtimeSensitive = @(
    "server.py",
    "main.py",
    "main_app.py",
    "ui.py",
    "config.py",
    "ReadOut.spec",
    "extension/manifest.json",
    "extension/popup.js"
)
$runtimeDelta = @($changedPaths | Where-Object { $_ -in $runtimeSensitive })
Write-TableRow -Check "Runtime-sensitive upstream paths" -Result ($(if ($runtimeDelta.Count -eq 0) { "PASS" } else { "REVIEW" })) -Detail (($runtimeDelta -join ", ") -replace "\|", "/")

Write-Host ""
Write-Host "## Upstream-only commits"
$commits = @(Invoke-GitText -GitArgs @("log", "--oneline", "--decorate", "--right-only", "HEAD...$Upstream"))
if ($commits.Count -eq 0) {
    Write-Host "None"
} else {
    $commits | ForEach-Object { Write-Host "- $_" }
}

Write-Host ""
Write-Host "## File delta vs upstream"
$delta = @(Invoke-GitText -GitArgs @("diff", "--name-status", "HEAD...$Upstream"))
if ($delta.Count -eq 0) {
    Write-Host "None"
} else {
    $delta | ForEach-Object { Write-Host $_ }
}

Write-Host ""
Write-Host "Next: review UPSTREAM_RECONCILIATION.md before merging or accepting any remote delta."

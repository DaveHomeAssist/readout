# Release readiness preflight for ReadOut.
# This script does not build packages. It reports whether this machine is ready
# to run the release checklist and can optionally run tests/live server checks.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [switch]$RunPytest,
    [switch]$RunSourceSmoke,
    [switch]$RunLiveChecks,
    [switch]$IncludeAudio
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$script:GitSafeDirectory = ((Resolve-Path ".").Path -replace "\\", "/")

function Add-Check {
    param(
        [string]$Check,
        [string]$Result,
        [string]$Detail
    )

    $results.Add([pscustomobject]@{
        Check = $Check
        Result = $Result
        Detail = $Detail
    })
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

function Get-PythonVersionText {
    param(
        [string]$Exe,
        [string[]]$BaseArgs = @()
    )

    try {
        $argv = @($BaseArgs + @("--version"))
        return (& $Exe @argv 2>&1 | Select-Object -First 1)
    } catch {
        return "version unavailable"
    }
}

function Resolve-SupportedPython {
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
            return [pscustomobject]@{
                Label = $candidate.Label
                Exe = $candidate.Exe
                Args = $candidate.Args
                Version = Get-PythonVersionText -Exe $candidate.Exe -BaseArgs $candidate.Args
            }
        }
    }

    return $null
}

function Test-PowerShellSyntax {
    param([string]$Path)

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Path), [ref]$tokens, [ref]$errors) > $null
    if ($errors.Count) {
        throw (($errors | ForEach-Object { $_.Message }) -join "; ")
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

Write-Host "ReadOut release preflight"
Write-Host "Working directory: $(Get-Location)"

$requiredFiles = @(
    "THREAT_MODEL.md",
    "FEATURE-SPEC.md",
    "UPSTREAM_RECONCILIATION.md",
    "ARCHITECT_SIGNOFF.md",
    "PACKAGING_VALIDATION.md",
    "MANUAL_SMOKE_VALIDATION.md",
    "RELEASE_CHECKLIST.md",
    "ROADMAP_STATUS.md",
    "MILESTONE_LOG.md",
    "ReadOut.spec",
    "build_windows.ps1",
    "build_mac.sh",
    "tools\secret_scan.ps1",
    "tools\architect_signoff_check.ps1",
    "tools\packaging_validation_check.ps1",
    "tools\manual_smoke_check.ps1",
    "tools\roadmap_audit.ps1",
    "tools\upstream_reconciliation.ps1",
    "tools\mac_package_smoke.sh",
    "tools\cors_origin_matrix.ps1",
    "tools\server_smoke.ps1",
    "tools\windows_packaging_prereqs.ps1",
    "tools\windows_package_smoke.ps1"
)

foreach ($file in $requiredFiles) {
    Add-Check -Check "Required file: $file" -Result ($(if (Test-Path $file) { "PASS" } else { "FAIL" })) -Detail $file
}

foreach ($script in @("tools\secret_scan.ps1", "tools\architect_signoff_check.ps1", "tools\packaging_validation_check.ps1", "tools\manual_smoke_check.ps1", "tools\roadmap_audit.ps1", "tools\upstream_reconciliation.ps1", "tools\cors_origin_matrix.ps1", "tools\server_smoke.ps1", "tools\windows_packaging_prereqs.ps1", "tools\windows_package_smoke.ps1", "tools\release_preflight.ps1", "build_windows.ps1")) {
    try {
        Test-PowerShellSyntax -Path $script
        Add-Check -Check "PowerShell syntax: $script" -Result "PASS" -Detail "parsed"
    } catch {
        Add-Check -Check "PowerShell syntax: $script" -Result "FAIL" -Detail $_.Exception.Message
    }
}

try {
    $inside = Invoke-GitText -GitArgs @("rev-parse", "--is-inside-work-tree")
    if (($inside | Select-Object -First 1) -eq "true") {
        try {
            $upstream = Invoke-GitText -GitArgs @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        } catch {
            $upstream = $null
        }
        if (-not $upstream) {
            Add-Check -Check "Git upstream currency" -Result "SKIP" -Detail "No upstream branch is configured."
        } else {
            $counts = Invoke-GitText -GitArgs @("rev-list", "--left-right", "--count", "HEAD...@{u}")
            if (-not $counts) {
                Add-Check -Check "Git upstream currency" -Result "FAIL" -Detail "Could not compare HEAD with upstream."
            } else {
                $parts = ($counts -split "\s+") | Where-Object { $_ -ne "" }
                $ahead = [int]$parts[0]
                $behind = [int]$parts[1]
                if ($behind -gt 0) {
                    Add-Check -Check "Git upstream currency" -Result "FAIL" -Detail "Branch is behind $upstream by $behind commit(s); ahead by $ahead."
                } else {
                    Add-Check -Check "Git upstream currency" -Result "PASS" -Detail "ahead=$ahead; behind=$behind vs $upstream"
                }
            }
        }
    } else {
        Add-Check -Check "Git upstream currency" -Result "SKIP" -Detail "Not a Git worktree."
    }
} catch {
    Add-Check -Check "Git upstream currency" -Result "FAIL" -Detail $_.Exception.Message
}

$python = Resolve-SupportedPython
if ($python) {
    Add-Check -Check "Python 3.10-3.12" -Result "PASS" -Detail "$($python.Version) via $($python.Label)"
} else {
    Add-Check -Check "Python 3.10-3.12" -Result "FAIL" -Detail "Install Python 3.12, 3.11, or 3.10 before packaging."
}

if (Get-Command espeak-ng -ErrorAction SilentlyContinue) {
    Add-Check -Check "espeak-ng on PATH" -Result "PASS" -Detail "found"
} else {
    Add-Check -Check "espeak-ng on PATH" -Result "FAIL" -Detail "Install espeak-ng and add it to PATH before packaging."
}

try {
    & .\tools\secret_scan.ps1 -Root . -Quiet
    Add-Check -Check "Secret scan" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "secret_scan.ps1 exit=$LASTEXITCODE"
} catch {
    Add-Check -Check "Secret scan" -Result "FAIL" -Detail $_.Exception.Message
}

try {
    & .\tools\architect_signoff_check.ps1 -Quiet
    Add-Check -Check "Architect sign-off" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "architect_signoff_check.ps1 exit=$LASTEXITCODE"
} catch {
    Add-Check -Check "Architect sign-off" -Result "FAIL" -Detail $_.Exception.Message
}

try {
    & .\tools\packaging_validation_check.ps1 -Quiet
    Add-Check -Check "Packaging validation evidence" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "packaging_validation_check.ps1 exit=$LASTEXITCODE"
} catch {
    Add-Check -Check "Packaging validation evidence" -Result "FAIL" -Detail $_.Exception.Message
}

try {
    & .\tools\manual_smoke_check.ps1 -Quiet
    Add-Check -Check "Manual smoke evidence" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "manual_smoke_check.ps1 exit=$LASTEXITCODE"
} catch {
    Add-Check -Check "Manual smoke evidence" -Result "FAIL" -Detail $_.Exception.Message
}

if ($RunPytest) {
    if (-not $python) {
        Add-Check -Check "python -m pytest" -Result "FAIL" -Detail "No supported Python was found."
    } else {
        try {
            $testArgs = @($python.Args + @("-m", "pytest"))
            & $python.Exe @testArgs
            Add-Check -Check "python -m pytest" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "exit=$LASTEXITCODE"
        } catch {
            Add-Check -Check "python -m pytest" -Result "FAIL" -Detail $_.Exception.Message
        }
    }
} else {
    Add-Check -Check "python -m pytest" -Result "SKIP" -Detail "Use -RunPytest to run the full suite."
}

if ($RunSourceSmoke) {
    if (-not $python) {
        Add-Check -Check "Source live HTTP smoke" -Result "FAIL" -Detail "No supported Python was found."
    } else {
        try {
            $smokeArgs = @($python.Args + @("-m", "pytest", "tests/test_live_http_smoke.py"))
            & $python.Exe @smokeArgs
            Add-Check -Check "Source live HTTP smoke" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "tests/test_live_http_smoke.py exit=$LASTEXITCODE"
        } catch {
            Add-Check -Check "Source live HTTP smoke" -Result "FAIL" -Detail $_.Exception.Message
        }
    }
} else {
    Add-Check -Check "Source live HTTP smoke" -Result "SKIP" -Detail "Use -RunSourceSmoke to run the in-process source server smoke."
}

if ($RunLiveChecks) {
    try {
        if ($IncludeAudio) {
            & .\tools\server_smoke.ps1 -BaseUrl $BaseUrl -IncludeAudio
        } else {
            & .\tools\server_smoke.ps1 -BaseUrl $BaseUrl
        }
        Add-Check -Check "Live server smoke" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "server_smoke.ps1 exit=$LASTEXITCODE"
    } catch {
        Add-Check -Check "Live server smoke" -Result "FAIL" -Detail $_.Exception.Message
    }

    try {
        & .\tools\cors_origin_matrix.ps1 -BaseUrl $BaseUrl
        Add-Check -Check "Live CORS matrix" -Result ($(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" })) -Detail "cors_origin_matrix.ps1 exit=$LASTEXITCODE"
    } catch {
        Add-Check -Check "Live CORS matrix" -Result "FAIL" -Detail $_.Exception.Message
    }
} else {
    Add-Check -Check "Live server smoke" -Result "SKIP" -Detail "Use -RunLiveChecks after starting ReadOut."
    Add-Check -Check "Live CORS matrix" -Result "SKIP" -Detail "Use -RunLiveChecks after starting ReadOut."
}

Write-Host ""
Write-Host "| Check | Result | Detail |"
Write-Host "|---|---|---|"
foreach ($row in $results) {
    Write-Host "| $($row.Check) | $($row.Result) | $($row.Detail) |"
}

if ($results.Result -contains "FAIL") {
    exit 1
}

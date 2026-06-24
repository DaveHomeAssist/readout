# Report Windows prerequisites for ReadOut packaging without installing or building.

param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Check,
        [string]$Result,
        [string]$Detail,
        [string]$NextAction
    )

    $results.Add([pscustomobject]@{
        Check = $Check
        Result = $Result
        Detail = $Detail
        NextAction = $NextAction
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

function Test-EspeakRuntime {
    param($Python)

    $espeak = Get-Command espeak-ng -ErrorAction SilentlyContinue
    if ($espeak) {
        return [pscustomobject]@{
            Ok = $true
            Detail = "system espeak-ng on PATH: $($espeak.Source)"
            NextAction = "Keep the runtime available before packaging."
        }
    }

    if (-not $Python) {
        return [pscustomobject]@{
            Ok = $false
            Detail = "No supported Python is available to check bundled espeakng_loader."
            NextAction = "Install Python 3.12, then run .\build_windows.ps1."
        }
    }

    $check = @"
import espeakng_loader
espeakng_loader.make_library_available()
print("bundled espeakng_loader")
"@
    try {
        $argv = @($Python.Args + @("-c", $check))
        $output = @(& $Python.Exe @argv 2>&1)
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{
                Ok = $true
                Detail = "bundled espeakng_loader via $($Python.Label)"
                NextAction = "Use .\build_windows.ps1 for the package build."
            }
        }
        return [pscustomobject]@{
            Ok = $false
            Detail = (($output -join " ") -replace "\s+", " ").Trim()
            NextAction = "Run .\build_windows.ps1 so requirements.txt installs espeakng-loader, or install the espeak-ng MSI."
        }
    } catch {
        return [pscustomobject]@{
            Ok = $false
            Detail = $_.Exception.Message
            NextAction = "Run .\build_windows.ps1 so requirements.txt installs espeakng-loader, or install the espeak-ng MSI."
        }
    }
}

Write-Host "ReadOut Windows packaging prerequisite report"
Write-Host "Working directory: $(Get-Location)"

$python = Resolve-SupportedPython
if ($python) {
    Add-Result `
        -Check "Python 3.10-3.12" `
        -Result "PASS" `
        -Detail "$($python.Version) via $($python.Label)" `
        -NextAction "Use .\build_windows.ps1 for the package build."
} else {
    $launcherText = ""
    if (Test-CommandAvailable "py") {
        $launcherLines = @(& py -0p 2>&1 | ForEach-Object { $_.ToString().Trim() } | Where-Object {
            $_ -and $_ -notmatch "System\.Management\.Automation\.RemoteException"
        })
        $launcherText = ($launcherLines -join " ").Trim()
    }
    if (-not $launcherText) {
        $launcherText = "No py launcher output."
    }
    Add-Result `
        -Check "Python 3.10-3.12" `
        -Result "FAIL" `
        -Detail $launcherText `
        -NextAction "Install Python 3.12, 3.11, or 3.10. Suggested winget ID: Python.Python.3.12"
}

$espeakRuntime = Test-EspeakRuntime -Python $python
if ($espeakRuntime.Ok) {
    Add-Result `
        -Check "eSpeak NG runtime" `
        -Result "PASS" `
        -Detail $espeakRuntime.Detail `
        -NextAction $espeakRuntime.NextAction
} else {
    Add-Result `
        -Check "eSpeak NG runtime" `
        -Result "FAIL" `
        -Detail $espeakRuntime.Detail `
        -NextAction $espeakRuntime.NextAction
}

if (Test-Path "dist\ReadOut\ReadOut.exe") {
    Add-Result `
        -Check "Existing Windows package" `
        -Result "PASS" `
        -Detail "dist\ReadOut\ReadOut.exe exists" `
        -NextAction "Run .\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe"
} else {
    Add-Result `
        -Check "Existing Windows package" `
        -Result "FAIL" `
        -Detail "dist\ReadOut\ReadOut.exe not found" `
        -NextAction "Run .\build_windows.ps1 after Python and an eSpeak NG runtime are available."
}

if (-not $Quiet) {
    Write-Host ""
    Write-Host "| Check | Result | Detail | Next Action |"
    Write-Host "|---|---|---|---|"
    foreach ($row in $results) {
        Write-Host "| $($row.Check) | $($row.Result) | $($row.Detail) | $($row.NextAction) |"
    }
}

if ($results.Result -contains "FAIL") {
    exit 1
}

exit 0

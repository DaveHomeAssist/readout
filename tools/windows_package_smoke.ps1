# Windows packaged-app smoke test.
# Run after .\build_windows.ps1 produces dist\ReadOut\ReadOut.exe.

param(
    [string]$ExePath = "dist\ReadOut\ReadOut.exe",
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [int]$TimeoutSec = 45,
    [switch]$IncludeAudio,
    [switch]$SkipCors
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$process = $null

function Add-Result {
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

function Test-ServerReady {
    try {
        $status = Invoke-RestMethod -Uri "$BaseUrl/status" -Method Get -TimeoutSec 2
        return [pscustomobject]@{
            Ready = $true
            Detail = "status=$($status.status); engine=$($status.engine)"
        }
    } catch {
        return [pscustomobject]@{
            Ready = $false
            Detail = $_.Exception.Message
        }
    }
}

function Invoke-Helper {
    param(
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    $powershellExe = (Get-Process -Id $PID).Path
    & $powershellExe -NoProfile -ExecutionPolicy Bypass -File (Resolve-Path $ScriptPath) @Arguments
    return $LASTEXITCODE
}

try {
    if (-not (Test-Path $ExePath)) {
        throw "Executable not found: $ExePath"
    }
    Add-Result -Check "Executable exists" -Result "PASS" -Detail $ExePath

    $preexisting = Test-ServerReady
    if ($preexisting.Ready) {
        throw "A server is already responding at $BaseUrl. Stop it before validating the packaged exe."
    }
    Add-Result -Check "Port available" -Result "PASS" -Detail $BaseUrl

    $resolvedExe = (Resolve-Path $ExePath).Path
    $process = Start-Process -FilePath $resolvedExe -PassThru -WindowStyle Hidden
    Add-Result -Check "Launch packaged exe" -Result "PASS" -Detail "pid=$($process.Id)"

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ready = $false
    $readyDetail = "timeout"
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) {
            throw "Packaged exe exited before server became ready. exit=$($process.ExitCode)"
        }

        $probe = Test-ServerReady
        if ($probe.Ready) {
            $ready = $true
            $readyDetail = $probe.Detail
            break
        }

        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "Server did not respond at $BaseUrl within $TimeoutSec seconds."
    }
    Add-Result -Check "Server ready" -Result "PASS" -Detail $readyDetail

    $smokeArgs = @("-BaseUrl", $BaseUrl)
    if ($IncludeAudio) {
        $smokeArgs += "-IncludeAudio"
    }
    $smokeExit = Invoke-Helper -ScriptPath ".\tools\server_smoke.ps1" -Arguments $smokeArgs
    Add-Result -Check "Non-audio server smoke" -Result ($(if ($smokeExit -eq 0) { "PASS" } else { "FAIL" })) -Detail "exit=$smokeExit"

    if (-not $SkipCors) {
        $corsExit = Invoke-Helper -ScriptPath ".\tools\cors_origin_matrix.ps1" -Arguments @("-BaseUrl", $BaseUrl)
        Add-Result -Check "CORS origin matrix" -Result ($(if ($corsExit -eq 0) { "PASS" } else { "FAIL" })) -Detail "exit=$corsExit"
    } else {
        Add-Result -Check "CORS origin matrix" -Result "SKIP" -Detail "SkipCors set"
    }
} catch {
    Add-Result -Check "Windows package smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Add-Result -Check "Stop packaged exe" -Result "PASS" -Detail "pid=$($process.Id)"
    }
}

Write-Host "| Check | Result | Detail |"
Write-Host "|---|---|---|"
foreach ($row in $results) {
    Write-Host "| $($row.Check) | $($row.Result) | $($row.Detail) |"
}

if ($results.Result -contains "FAIL") {
    exit 1
}

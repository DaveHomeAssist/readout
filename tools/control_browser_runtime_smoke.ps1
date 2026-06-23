# Runtime non-audio smoke for the browser `/control` UI.
# Starts a temporary source server, opens `/control` in headless Chrome/Edge,
# verifies that the JavaScript-rendered status display reflects `/status`,
# then stops the server and removes the temporary browser profile.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [int]$TimeoutSec = 45,
    [string]$PythonExe = "python",
    [string]$BrowserExe = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$process = $null
$stdoutLog = Join-Path $env:TEMP "readout-control-browser-smoke-$PID.stdout.log"
$stderrLog = Join-Path $env:TEMP "readout-control-browser-smoke-$PID.stderr.log"
$userDataDir = Join-Path $env:TEMP "readout-control-browser-profile-$PID"

function Add-Result {
    param(
        [string]$Check,
        [string]$Result,
        [string]$Detail
    )

    $results.Add([pscustomobject]@{
        Check = $Check
        Result = $Result
        Detail = (($Detail -replace "\|", "/") -replace "\s+", " ").Trim()
    })
}

function Limit-Detail {
    param([string]$Text, [int]$Length = 160)

    $cleaned = (($Text -replace "\|", "/") -replace "\s+", " ").Trim()
    if ($cleaned.Length -le $Length) {
        return $cleaned
    }

    return $cleaned.Substring(0, $Length) + "..."
}

function Assert-LoopbackBaseUrl {
    $uri = [uri]$BaseUrl
    if ($uri.Scheme -ne "http") {
        throw "Unsupported BaseUrl scheme: $($uri.Scheme)"
    }
    if ($uri.Host -notin @("127.0.0.1", "localhost")) {
        throw "Refusing browser runtime smoke against non-loopback host: $($uri.Host)"
    }
    if ($uri.Port -le 0) {
        throw "BaseUrl must include a concrete port."
    }
}

function Resolve-Browser {
    if ($BrowserExe) {
        if (-not (Test-Path $BrowserExe)) {
            throw "BrowserExe not found: $BrowserExe"
        }
        return (Resolve-Path $BrowserExe).Path
    }

    $programFiles = [Environment]::GetFolderPath("ProgramFiles")
    $programFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $localAppData = $env:LOCALAPPDATA
    $candidates = @(
        "$programFiles\Google\Chrome\Application\chrome.exe",
        "$programFilesX86\Google\Chrome\Application\chrome.exe",
        "$localAppData\Google\Chrome\Application\chrome.exe",
        "$programFiles\Microsoft\Edge\Application\msedge.exe",
        "$programFilesX86\Microsoft\Edge\Application\msedge.exe",
        "$localAppData\Microsoft\Edge\Application\msedge.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "Chrome or Edge was not found. Pass -BrowserExe to validate with a specific Chromium browser."
}

function Test-ServerReady {
    try {
        $status = Invoke-RestMethod -Uri "$BaseUrl/status" -Method Get -TimeoutSec 2
        return [pscustomobject]@{
            Ready = $true
            Status = $status
            Detail = "status=$($status.status); engine=$($status.engine); dependency_issues=$($status.dependency_issues.Count)"
        }
    } catch {
        return [pscustomobject]@{
            Ready = $false
            Status = $null
            Detail = $_.Exception.Message
        }
    }
}

function ConvertTo-ProcessArguments {
    param([string[]]$Args)

    return (($Args | ForEach-Object {
        '"' + ($_ -replace '"', '\"') + '"'
    }) -join " ")
}

function Invoke-BrowserDomDump {
    param(
        [string]$BrowserPath,
        [string]$Url
    )

    New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null

    $args = @(
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--user-data-dir=$userDataDir",
        "--virtual-time-budget=5000",
        "--dump-dom",
        $Url
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $BrowserPath
    try {
        foreach ($arg in $args) {
            [void]$startInfo.ArgumentList.Add($arg)
        }
    } catch {
        $startInfo.Arguments = ConvertTo-ProcessArguments -Args $args
    }
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $browser = [System.Diagnostics.Process]::Start($startInfo)
    $stdoutTask = $browser.StandardOutput.ReadToEndAsync()
    $stderrTask = $browser.StandardError.ReadToEndAsync()
    if (-not $browser.WaitForExit(20000)) {
        $browser.Kill($true)
        throw "Browser timed out while dumping /control DOM."
    }

    return [pscustomobject]@{
        ExitCode = $browser.ExitCode
        Dom = $stdoutTask.GetAwaiter().GetResult()
        Error = $stderrTask.GetAwaiter().GetResult()
    }
}

function Get-HtmlMatch {
    param([string]$Html, [string]$Pattern)

    $match = [regex]::Match($Html, $Pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) {
        return $null
    }

    return [System.Net.WebUtility]::HtmlDecode($match.Groups[1].Value.Trim())
}

try {
    Assert-LoopbackBaseUrl

    $uri = [uri]$BaseUrl
    $preexisting = Test-ServerReady
    if ($preexisting.Ready) {
        throw "A server is already responding at $BaseUrl. Stop it before validating the browser runtime workflow."
    }
    Add-Result -Check "Port available" -Result "PASS" -Detail $BaseUrl

    $browserPath = Resolve-Browser
    Add-Result -Check "Chromium browser available" -Result "PASS" -Detail $browserPath

    $process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "$($uri.Port)") `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog
    Add-Result -Check "Launch source server" -Result "PASS" -Detail "pid=$($process.Id)"

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ready = $false
    $readyStatus = $null
    $readyDetail = "timeout"
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) {
            throw "Source server exited before ready. exit=$($process.ExitCode)"
        }

        $probe = Test-ServerReady
        if ($probe.Ready) {
            $ready = $true
            $readyStatus = $probe.Status
            $readyDetail = $probe.Detail
            break
        }

        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "Source server did not respond at $BaseUrl within $TimeoutSec seconds."
    }
    Add-Result -Check "Server ready" -Result "PASS" -Detail $readyDetail

    $dump = Invoke-BrowserDomDump -BrowserPath $browserPath -Url "$BaseUrl/control"
    if ($dump.ExitCode -ne 0) {
        throw "Browser DOM dump failed with exit=$($dump.ExitCode): $(Limit-Detail -Text $dump.Error)"
    }

    $statusState = Get-HtmlMatch -Html $dump.Dom -Pattern '<div id="status" class="status" data-state="([^"]+)"'
    $statusLabel = Get-HtmlMatch -Html $dump.Dom -Pattern '<span id="statusLabel">([^<]+)</span>'
    $feedback = Get-HtmlMatch -Html $dump.Dom -Pattern '<div class="feedback" id="feedback"[^>]*>(.*?)</div>'

    if (-not $statusState -or -not $statusLabel -or -not $feedback) {
        throw "Rendered /control DOM did not include status state, label, and feedback nodes."
    }

    $expectedState = [string]$readyStatus.status
    $passed = ($statusState -eq $expectedState -and $statusLabel -ne "Offline" -and $feedback -notmatch "Waiting for local server status")
    $detail = "state=$statusState; label=$statusLabel; feedback=$(Limit-Detail -Text $feedback -Length 120)"
    Add-Result -Check "/control status display updates" -Result ($(if ($passed) { "PASS" } else { "FAIL" })) -Detail $detail
} catch {
    Add-Result -Check "Control browser runtime smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop source server" -Result "PASS" -Detail "pid=$($process.Id)"
    }

    if (Test-Path $userDataDir) {
        Remove-Item -LiteralPath $userDataDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not $Quiet) {
    Write-Host "| Check | Result | Detail |"
    Write-Host "|---|---|---|"
    foreach ($row in $results) {
        Write-Host "| $($row.Check) | $($row.Result) | $($row.Detail) |"
    }
}

if ($results.Result -contains "FAIL") {
    exit 1
}

exit 0

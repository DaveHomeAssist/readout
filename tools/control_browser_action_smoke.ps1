# Runtime action smoke for the browser `/control` UI.
# Starts a temporary source server, opens `/control` in headless Chrome/Edge,
# clicks Preview, Speak, Save WAV, and Stop through the real page JavaScript,
# verifies the created WAV file exists, then restores local config/history.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [int]$TimeoutSec = 120,
    [string]$PythonExe = "python",
    [string]$BrowserExe = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$process = $null
$browser = $null
$socket = $null
$stdoutLog = Join-Path $env:TEMP "readout-control-action-smoke-$PID.stdout.log"
$stderrLog = Join-Path $env:TEMP "readout-control-action-smoke-$PID.stderr.log"
$browserStdoutLog = Join-Path $env:TEMP "readout-control-action-browser-$PID.stdout.log"
$browserStderrLog = Join-Path $env:TEMP "readout-control-action-browser-$PID.stderr.log"
$userDataDir = Join-Path $env:TEMP "readout-control-action-profile-$PID"
$savedWavPath = $null
$homeReadout = Join-Path $HOME ".readout"
$configPath = Join-Path $homeReadout "config.json"
$historyPath = Join-Path $homeReadout "history.json"
$configBackup = $null
$historyBackup = $null
$configExisted = Test-Path $configPath
$historyExisted = Test-Path $historyPath
$script:MessageId = 0

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
    param([string]$Text, [int]$Length = 180)

    $cleaned = (($Text -replace "\|", "/") -replace "\s+", " ").Trim()
    if ($cleaned.Length -le $Length) {
        return $cleaned
    }

    return $cleaned.Substring(0, $Length) + "..."
}

function Backup-File {
    param([string]$Path)

    if (Test-Path $Path) {
        return [System.IO.File]::ReadAllBytes((Resolve-Path $Path))
    }

    return $null
}

function Restore-File {
    param(
        [string]$Path,
        [byte[]]$Bytes,
        [bool]$Existed
    )

    if ($Existed) {
        $dir = Split-Path -Parent $Path
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        [System.IO.File]::WriteAllBytes($Path, $Bytes)
    } elseif (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Force
    }
}

function Assert-LoopbackBaseUrl {
    $uri = [uri]$BaseUrl
    if ($uri.Scheme -ne "http") {
        throw "Unsupported BaseUrl scheme: $($uri.Scheme)"
    }
    if ($uri.Host -notin @("127.0.0.1", "localhost")) {
        throw "Refusing browser action smoke against non-loopback host: $($uri.Host)"
    }
    if ($uri.Port -le 0) {
        throw "BaseUrl must include a concrete port."
    }
}

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), 0)
    $listener.Start()
    try {
        return $listener.LocalEndpoint.Port
    } finally {
        $listener.Stop()
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

function Start-ControlBrowser {
    param(
        [string]$BrowserPath,
        [int]$DebugPort
    )

    New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null
    $args = @(
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--remote-debugging-port=$DebugPort",
        "--user-data-dir=$userDataDir",
        "$BaseUrl/control"
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

    $started = [System.Diagnostics.Process]::Start($startInfo)
    return $started
}

function Get-DevToolsWebSocketUrl {
    param([int]$DebugPort)

    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        try {
            $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/list" -Method Get -TimeoutSec 2
            foreach ($target in $targets) {
                if ($target.type -eq "page" -and $target.url -like "$BaseUrl/control*") {
                    return $target.webSocketDebuggerUrl
                }
            }
        } catch {
            Start-Sleep -Milliseconds 250
        }
        Start-Sleep -Milliseconds 250
    }

    throw "DevTools page target was not available."
}

function Connect-Cdp {
    param([string]$WebSocketUrl)

    $client = [System.Net.WebSockets.ClientWebSocket]::new()
    [void]$client.ConnectAsync([uri]$WebSocketUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
    return $client
}

function Invoke-Cdp {
    param(
        [System.Net.WebSockets.ClientWebSocket]$Client,
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $script:MessageId += 1
    $id = $script:MessageId
    $payload = @{
        id = $id
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 20 -Compress

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    [void]$Client.SendAsync(
        [ArraySegment[byte]]::new($bytes),
        [System.Net.WebSockets.WebSocketMessageType]::Text,
        $true,
        [Threading.CancellationToken]::None
    ).GetAwaiter().GetResult()

    $buffer = New-Object byte[] 131072
    $builder = [System.Text.StringBuilder]::new()
    while ($true) {
        $result = $Client.ReceiveAsync(
            [ArraySegment[byte]]::new($buffer),
            [Threading.CancellationToken]::None
        ).GetAwaiter().GetResult()

        if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
            throw "DevTools websocket closed."
        }

        [void]$builder.Append([System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count))
        if (-not $result.EndOfMessage) {
            continue
        }

        $messageText = $builder.ToString()
        $builder.Clear() | Out-Null
        $message = $messageText | ConvertFrom-Json
        if ($message.id -eq $id) {
            if ($message.error) {
                throw "CDP $Method failed: $($message.error.message)"
            }
            return $message
        }
    }
}

function Invoke-CdpExpression {
    param(
        [System.Net.WebSockets.ClientWebSocket]$Client,
        [string]$Expression,
        [switch]$AwaitPromise
    )

    $params = @{
        expression = $Expression
        returnByValue = $true
        awaitPromise = [bool]$AwaitPromise
    }
    $message = Invoke-Cdp -Client $Client -Method "Runtime.evaluate" -Params $params
    if ($message.result.exceptionDetails) {
        throw "Browser expression failed: $($message.result.exceptionDetails.text)"
    }
    return $message.result.result.value
}

try {
    Assert-LoopbackBaseUrl

    $uri = [uri]$BaseUrl
    $preexisting = Test-ServerReady
    if ($preexisting.Ready) {
        throw "A server is already responding at $BaseUrl. Stop it before validating the browser action workflow."
    }
    Add-Result -Check "Port available" -Result "PASS" -Detail $BaseUrl

    $configBackup = Backup-File -Path $configPath
    $historyBackup = Backup-File -Path $historyPath
    Add-Result -Check "Backup local config/history" -Result "PASS" -Detail "config=$configExisted; history=$historyExisted"

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

    $configBody = @{
        engine = "kokoro"
        voice = "af_heart"
        speed = 1.0
        history_enabled = $false
    } | ConvertTo-Json -Compress
    Invoke-RestMethod -Uri "$BaseUrl/config" -Method Patch -ContentType "application/json" -Body $configBody -TimeoutSec 5 | Out-Null
    Add-Result -Check "Prepare Kokoro config" -Result "PASS" -Detail "engine=kokoro; voice=af_heart; speed=1.0; history_enabled=false"

    $debugPort = Get-FreeTcpPort
    $browser = Start-ControlBrowser -BrowserPath $browserPath -DebugPort $debugPort
    Add-Result -Check "Launch headless browser" -Result "PASS" -Detail "pid=$($browser.Id); debugPort=$debugPort"

    $wsUrl = Get-DevToolsWebSocketUrl -DebugPort $debugPort
    $socket = Connect-Cdp -WebSocketUrl $wsUrl
    Invoke-Cdp -Client $socket -Method "Runtime.enable" | Out-Null

    $readyExpression = @"
(() => {
  const status = document.querySelector("#statusLabel")?.textContent || "";
  const feedback = document.querySelector("#feedback")?.textContent || "";
  return { status, feedback };
})()
"@
    $pageState = Invoke-CdpExpression -Client $socket -Expression $readyExpression
    Add-Result -Check "Browser connected to /control" -Result "PASS" -Detail "status=$($pageState.status); feedback=$(Limit-Detail -Text $pageState.feedback)"

    $previewExpression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const preview = document.querySelector("#previewBtn");
  const feedback = document.querySelector("#feedback");
  if (!preview || !feedback) return { ok: false, feedback: "preview controls missing" };
  preview.click();
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    const message = feedback.textContent || "";
    if (message.includes("Preview playing.")) return { ok: true, feedback: message };
    if (message.includes("failed") || message.includes("Dependency issue") || message.includes("Could not reach")) {
      return { ok: false, feedback: message };
    }
    await wait(500);
  }
  return { ok: false, feedback: feedback.textContent || "timed out waiting for preview" };
})()
"@
    $previewResult = Invoke-CdpExpression -Client $socket -Expression $previewExpression -AwaitPromise
    if (-not $previewResult.ok) {
        throw "Preview Voice action failed: $($previewResult.feedback)"
    }
    Add-Result -Check "/control Preview Voice action" -Result "PASS" -Detail (Limit-Detail -Text $previewResult.feedback)

    $speakExpression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const text = document.querySelector("#text");
  const speak = document.querySelector("#speakBtn");
  const feedback = document.querySelector("#feedback");
  if (!text || !speak || !feedback) return { ok: false, feedback: "speak controls missing" };
  text.value = "ReadOut browser action smoke. Speak this through the source control panel.";
  text.dispatchEvent(new Event("input", { bubbles: true }));
  speak.click();
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    const message = feedback.textContent || "";
    if (message.includes("Playing")) return { ok: true, feedback: message };
    if (message.includes("failed") || message.includes("Dependency issue") || message.includes("Could not reach")) {
      return { ok: false, feedback: message };
    }
    await wait(500);
  }
  return { ok: false, feedback: feedback.textContent || "timed out waiting for speak" };
})()
"@
    $speakResult = Invoke-CdpExpression -Client $socket -Expression $speakExpression -AwaitPromise
    if (-not $speakResult.ok) {
        throw "Speak action failed: $($speakResult.feedback)"
    }
    Add-Result -Check "/control Speak action" -Result "PASS" -Detail (Limit-Detail -Text $speakResult.feedback)

    $saveExpression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const text = document.querySelector("#text");
  const save = document.querySelector("#saveBtn");
  const feedback = document.querySelector("#feedback");
  if (!text || !save || !feedback) return { ok: false, feedback: "required controls missing" };
  text.value = "ReadOut browser action smoke. Save this as a WAV file.";
  text.dispatchEvent(new Event("input", { bubbles: true }));
  save.click();
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    const message = feedback.textContent || "";
    if (message.startsWith("Saved to ")) return { ok: true, feedback: message };
    if (message.includes("failed") || message.includes("Dependency issue") || message.includes("Could not reach")) {
      return { ok: false, feedback: message };
    }
    await wait(500);
  }
  return { ok: false, feedback: feedback.textContent || "timed out waiting for save" };
})()
"@
    $saveResult = Invoke-CdpExpression -Client $socket -Expression $saveExpression -AwaitPromise
    if (-not $saveResult.ok) {
        throw "Save WAV action failed: $($saveResult.feedback)"
    }
    $savedWavPath = ([string]$saveResult.feedback).Substring("Saved to ".Length)
    Add-Result -Check "/control Save WAV action" -Result "PASS" -Detail (Limit-Detail -Text $saveResult.feedback)

    if (-not (Test-Path $savedWavPath)) {
        throw "Saved WAV not found: $savedWavPath"
    }
    $savedFile = Get-Item -LiteralPath $savedWavPath
    if ($savedFile.Length -le 44) {
        throw "Saved WAV is too small: $($savedFile.Length) bytes"
    }
    Add-Result -Check "Saved WAV file exists" -Result "PASS" -Detail "$savedWavPath ($($savedFile.Length) bytes)"

    $stopExpression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const stop = document.querySelector("#stopBtn");
  const feedback = document.querySelector("#feedback");
  if (!stop || !feedback) return { ok: false, feedback: "stop controls missing" };
  stop.click();
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    const message = feedback.textContent || "";
    if (message.includes("Playback stopped.")) return { ok: true, feedback: message };
    await wait(250);
  }
  return { ok: false, feedback: feedback.textContent || "timed out waiting for stop" };
})()
"@
    $stopResult = Invoke-CdpExpression -Client $socket -Expression $stopExpression -AwaitPromise
    Add-Result -Check "/control Stop action" -Result ($(if ($stopResult.ok) { "PASS" } else { "FAIL" })) -Detail (Limit-Detail -Text $stopResult.feedback)
} catch {
    Add-Result -Check "Control browser action smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    if ($socket) {
        try {
            $socket.Dispose()
        } catch {}
    }

    if ($browser -and -not $browser.HasExited) {
        Stop-Process -Id $browser.Id -Force
        Wait-Process -Id $browser.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop headless browser" -Result "PASS" -Detail "pid=$($browser.Id)"
    }

    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop source server" -Result "PASS" -Detail "pid=$($process.Id)"
    }

    if ($savedWavPath -and (Test-Path $savedWavPath)) {
        Remove-Item -LiteralPath $savedWavPath -Force -ErrorAction SilentlyContinue
    }

    Restore-File -Path $configPath -Bytes $configBackup -Existed $configExisted
    Restore-File -Path $historyPath -Bytes $historyBackup -Existed $historyExisted
    Add-Result -Check "Restore local config/history" -Result "PASS" -Detail "config/history restored"

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

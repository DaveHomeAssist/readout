# Runtime non-audio smoke for the Chrome/Edge extension popup.
# Loads the unpacked extension, verifies OFFLINE/READY popup states, allowlists
# the real extension origin, clicks Preview and Stop, then restores local
# config/history.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [string]$ExtensionDir = "extension",
    [int]$TimeoutSec = 60,
    [string]$PythonExe = "python",
    [string]$BrowserExe = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$browser = $null
$server = $null
$socket = $null
$stdoutLog = Join-Path $env:TEMP "readout-extension-runtime-$PID.stdout.log"
$stderrLog = Join-Path $env:TEMP "readout-extension-runtime-$PID.stderr.log"
$userDataDir = Join-Path $env:TEMP "readout-extension-runtime-profile-$PID"
$homeReadout = Join-Path $HOME ".readout"
$configPath = Join-Path $homeReadout "config.json"
$historyPath = Join-Path $homeReadout "history.json"
$configExisted = Test-Path $configPath
$historyExisted = Test-Path $historyPath
$configBackup = $null
$historyBackup = $null
$script:MessageId = 0

function Add-Result {
    param([string]$Check, [string]$Result, [string]$Detail)

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
    param([string]$Path, [byte[]]$Bytes, [bool]$Existed)

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
        throw "Refusing extension runtime smoke against non-loopback host: $($uri.Host)"
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
    return (($Args | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join " ")
}

function Start-ExtensionBrowser {
    param([string]$BrowserPath, [int]$DebugPort, [string]$ResolvedExtensionDir)

    New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null
    $args = @(
        "--remote-debugging-port=$DebugPort",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=800,600",
        "--window-position=-32000,-32000",
        "--user-data-dir=$userDataDir",
        "about:blank"
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

    return [System.Diagnostics.Process]::Start($startInfo)
}

function Wait-DevTools {
    param([int]$DebugPort)

    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/version" -Method Get -TimeoutSec 2 | Out-Null
            return
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    throw "DevTools endpoint was not available."
}

function Get-BrowserWebSocketUrl {
    param([int]$DebugPort)

    $version = Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/version" -Method Get -TimeoutSec 2
    if (-not $version.webSocketDebuggerUrl) {
        throw "DevTools browser websocket was not available."
    }
    return $version.webSocketDebuggerUrl
}

function Load-UnpackedExtension {
    param([int]$DebugPort, [string]$ResolvedExtensionDir)

    $browserSocket = $null
    try {
        $browserSocket = Connect-Cdp -WebSocketUrl (Get-BrowserWebSocketUrl -DebugPort $DebugPort)
        $message = Invoke-Cdp -Client $browserSocket -Method "Extensions.loadUnpacked" -Params @{
            path = $ResolvedExtensionDir
        }
        $id = $message.result.id
        if (-not $id) {
            throw "DevTools did not return an extension ID."
        }
        return $id
    } finally {
        if ($browserSocket) {
            try { $browserSocket.Dispose() } catch {}
        }
    }
}

function Get-PageWebSocketUrl {
    param([int]$DebugPort)

    $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/list" -Method Get -TimeoutSec 2
    foreach ($target in $targets) {
        if ($target.type -eq "page" -and $target.webSocketDebuggerUrl) {
            return $target.webSocketDebuggerUrl
        }
    }
    throw "No page target was available."
}

function Get-ServiceWorkerWebSocketUrl {
    param([int]$DebugPort, [string]$ExtensionId)

    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/list" -Method Get -TimeoutSec 2
        foreach ($target in $targets) {
            if ($target.type -eq "service_worker" -and $target.url -like "chrome-extension://$ExtensionId/*" -and $target.webSocketDebuggerUrl) {
                return $target.webSocketDebuggerUrl
            }
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Extension service worker target was not available."
}

function Open-ExtensionActionPopup {
    param([int]$DebugPort, [string]$ExtensionId)

    $browserSocket = $null
    try {
        $browserSocket = Connect-Cdp -WebSocketUrl (Get-BrowserWebSocketUrl -DebugPort $DebugPort)
        $created = Invoke-Cdp -Client $browserSocket -Method "Target.createTarget" -Params @{
            url = "about:blank"
        }
        $targetId = $created.result.targetId
        if (-not $targetId) {
            throw "Could not create tab target for extension action trigger."
        }
        $targets = Invoke-Cdp -Client $browserSocket -Method "Target.getTargets"
        $targetSummary = (($targets.result.targetInfos | ForEach-Object {
            "$($_.type):$($_.targetId):$($_.url)"
        }) -join "; ")
        foreach ($target in $targets.result.targetInfos) {
            if ($target.type -eq "tab" -and $target.url -eq "about:blank") {
                $targetId = $target.targetId
                break
            }
        }
        try {
            Invoke-Cdp -Client $browserSocket -Method "Extensions.triggerAction" -Params @{
                id = $ExtensionId
                targetId = $targetId
            } | Out-Null
        } catch {
            throw "$($_.Exception.Message); targets=$(Limit-Detail -Text $targetSummary -Length 500)"
        }
    } finally {
        if ($browserSocket) {
            try { $browserSocket.Dispose() } catch {}
        }
    }

    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/list" -Method Get -TimeoutSec 2
        foreach ($target in $targets) {
            if ($target.url -eq "chrome-extension://$ExtensionId/popup.html" -and $target.webSocketDebuggerUrl) {
                return $target.webSocketDebuggerUrl
            }
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Extension action popup target was not available."
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
    $payload = @{ id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 20 -Compress
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

    $message = Invoke-Cdp -Client $Client -Method "Runtime.evaluate" -Params @{
        expression = $Expression
        returnByValue = $true
        awaitPromise = [bool]$AwaitPromise
    }
    if ($message.result.exceptionDetails) {
        throw "Browser expression failed: $($message.result.exceptionDetails.text)"
    }
    return $message.result.result.value
}

function Navigate-Popup {
    param([System.Net.WebSockets.ClientWebSocket]$Client, [string]$ExtensionId)

    Invoke-Cdp -Client $Client -Method "Page.navigate" -Params @{ url = "chrome-extension://$ExtensionId/popup.html" } | Out-Null
    Wait-PopupRendered -Client $Client
}

function Wait-PopupRendered {
    param([System.Net.WebSockets.ClientWebSocket]$Client)

    $expression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    if (document.readyState === "complete" && document.querySelector("#status") && document.querySelector("#status-detail")) return true;
    await wait(100);
  }
  return false;
})()
"@
    $ready = Invoke-CdpExpression -Client $Client -Expression $expression -AwaitPromise
    if (-not $ready) {
        $diagnostic = Invoke-CdpExpression -Client $Client -Expression @"
(() => ({
  href: location.href,
  readyState: document.readyState,
  title: document.title,
  body: (document.body?.innerText || "").slice(0, 200)
}))()
"@
        throw "Popup did not finish rendering. href=$($diagnostic.href); readyState=$($diagnostic.readyState); title=$($diagnostic.title); body=$(Limit-Detail -Text $diagnostic.body)"
    }
}

function Invoke-PopupStatusRefresh {
    param([System.Net.WebSockets.ClientWebSocket]$Client)

    $expression = @"
(async () => {
  if (typeof checkStatus !== "function") return false;
  await checkStatus();
  return true;
})()
"@
    return Invoke-CdpExpression -Client $Client -Expression $expression -AwaitPromise
}

function Get-PopupState {
    param([System.Net.WebSockets.ClientWebSocket]$Client)

    $expression = @"
(() => ({
  status: document.querySelector("#status")?.textContent || "",
  statusClass: document.querySelector("#status")?.className || "",
  detail: document.querySelector("#status-detail")?.textContent || "",
  voiceCount: document.querySelector("#voice")?.options.length || 0
}))()
"@
    return Invoke-CdpExpression -Client $Client -Expression $expression
}

function Wait-PopupStatus {
    param([System.Net.WebSockets.ClientWebSocket]$Client, [string]$Expected)

    $deadline = (Get-Date).AddSeconds(15)
    $state = $null
    while ((Get-Date) -lt $deadline) {
        $state = Get-PopupState -Client $Client
        if ($state.status -eq $Expected) {
            return $state
        }
        Start-Sleep -Milliseconds 250
    }
    return $state
}

try {
    Assert-LoopbackBaseUrl
    if (-not (Test-Path $ExtensionDir)) {
        throw "ExtensionDir not found: $ExtensionDir"
    }
    $resolvedExtensionDir = (Resolve-Path $ExtensionDir).Path

    $preexisting = Test-ServerReady
    if ($preexisting.Ready) {
        throw "A server is already responding at $BaseUrl. Stop it before validating extension runtime state."
    }
    Add-Result -Check "Port available" -Result "PASS" -Detail $BaseUrl

    $configBackup = Backup-File -Path $configPath
    $historyBackup = Backup-File -Path $historyPath
    Add-Result -Check "Backup local config/history" -Result "PASS" -Detail "config=$configExisted; history=$historyExisted"

    $browserPath = Resolve-Browser
    $debugPort = Get-FreeTcpPort
    $browser = Start-ExtensionBrowser -BrowserPath $browserPath -DebugPort $debugPort -ResolvedExtensionDir $resolvedExtensionDir
    Add-Result -Check "Launch extension browser" -Result "PASS" -Detail "pid=$($browser.Id); debugPort=$debugPort"

    Wait-DevTools -DebugPort $debugPort
    $extensionId = Load-UnpackedExtension -DebugPort $debugPort -ResolvedExtensionDir $resolvedExtensionDir
    $extensionOrigin = "chrome-extension://$extensionId"
    Add-Result -Check "Load unpacked extension" -Result "PASS" -Detail $extensionOrigin

    $openedViaAction = $false
    try {
        $socket = Connect-Cdp -WebSocketUrl (Open-ExtensionActionPopup -DebugPort $debugPort -ExtensionId $extensionId)
        $openedViaAction = $true
        Add-Result -Check "Open extension action popup" -Result "PASS" -Detail $extensionOrigin
    } catch {
        Add-Result -Check "Open extension action popup" -Result "SKIP" -Detail (Limit-Detail -Text $_.Exception.Message)
        $socket = Connect-Cdp -WebSocketUrl (Get-PageWebSocketUrl -DebugPort $debugPort)
    }
    Invoke-Cdp -Client $socket -Method "Runtime.enable" | Out-Null
    Invoke-Cdp -Client $socket -Method "Page.enable" | Out-Null

    if ($openedViaAction) {
        Wait-PopupRendered -Client $socket
    } else {
        Navigate-Popup -Client $socket -ExtensionId $extensionId
    }
    Invoke-PopupStatusRefresh -Client $socket | Out-Null
    $offline = Wait-PopupStatus -Client $socket -Expected "OFFLINE"
    if ($offline.status -ne "OFFLINE" -or $offline.detail -notmatch "Server offline") {
        $state = Get-PopupState -Client $socket
        $diagnostic = Invoke-CdpExpression -Client $socket -Expression @"
(async () => {
  let manual = null;
  if (typeof checkStatus === "function") {
    await checkStatus();
    manual = {
      status: document.querySelector("#status")?.textContent || "",
      detail: document.querySelector("#status-detail")?.textContent || ""
    };
  }
  return {
    scripts: Array.from(document.scripts).map((script) => script.src || script.textContent.slice(0, 40)),
    scriptTail: await fetch(chrome.runtime.getURL("popup.js")).then((res) => res.text()).then((text) => text.slice(-220)),
    abortTimeout: typeof AbortSignal?.timeout,
    fetchWithTimeout: typeof fetchWithTimeout,
    checkStatus: typeof checkStatus,
    chromeTabs: typeof chrome?.tabs,
    chromeScripting: typeof chrome?.scripting,
    manual
  };
})()
"@ -AwaitPromise
        throw "Popup offline state did not render expected next action: status=$($offline.status); detail=$($offline.detail); voiceCount=$($state.voiceCount); abortTimeout=$($diagnostic.abortTimeout); fetchWithTimeout=$($diagnostic.fetchWithTimeout); checkStatus=$($diagnostic.checkStatus); manualStatus=$($diagnostic.manual.status); manualDetail=$($diagnostic.manual.detail); chromeTabs=$($diagnostic.chromeTabs); scriptTail=$(Limit-Detail -Text $diagnostic.scriptTail); scripts=$($diagnostic.scripts -join ',')"
    }
    Add-Result -Check "Popup OFFLINE state" -Result "PASS" -Detail (Limit-Detail -Text $offline.detail)

    $uri = [uri]$BaseUrl
    $server = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "$($uri.Port)") `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog
    Add-Result -Check "Launch source server" -Result "PASS" -Detail "pid=$($server.Id)"

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ready = $false
    $readyDetail = "timeout"
    while ((Get-Date) -lt $deadline) {
        if ($server.HasExited) {
            throw "Source server exited before ready. exit=$($server.ExitCode)"
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
        throw "Source server did not respond at $BaseUrl within $TimeoutSec seconds."
    }
    Add-Result -Check "Server ready" -Result "PASS" -Detail $readyDetail

    $configBody = @{
        allowed_origins = @($extensionOrigin)
        engine = "kokoro"
        voice = "af_heart"
        speed = 1.0
    } | ConvertTo-Json -Compress
    Invoke-RestMethod -Uri "$BaseUrl/config" -Method Patch -ContentType "application/json" -Body $configBody -TimeoutSec 5 | Out-Null
    Add-Result -Check "Extension origin allowlisted" -Result "PASS" -Detail $extensionOrigin

    Navigate-Popup -Client $socket -ExtensionId $extensionId
    Invoke-PopupStatusRefresh -Client $socket | Out-Null
    $readyState = Wait-PopupStatus -Client $socket -Expected "READY"
    if ($readyState.status -ne "READY" -or $readyState.detail -notmatch "Server connected") {
        throw "Popup READY state did not render expected detail: status=$($readyState.status); detail=$($readyState.detail)"
    }
    Add-Result -Check "Popup READY state" -Result "PASS" -Detail (Limit-Detail -Text $readyState.detail)

    $previewExpression = @"
(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const button = document.querySelector("#btn-preview");
  if (!button) {
    return { ok: false, detail: "Preview button missing" };
  }
  button.click();
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    const status = document.querySelector("#status")?.textContent || "";
    const detail = document.querySelector("#status-detail")?.textContent || "";
    if (status === "READY" && detail.includes("Previewing")) {
      return { ok: true, detail };
    }
    if (status === "ERROR" || status === "OFFLINE") {
      return { ok: false, detail };
    }
    await wait(500);
  }
  return {
    ok: false,
    detail: document.querySelector("#status-detail")?.textContent || "timed out waiting for preview"
  };
})()
"@
    $preview = Invoke-CdpExpression -Client $socket -Expression $previewExpression -AwaitPromise
    Add-Result -Check "Popup Preview action" -Result ($(if ($preview.ok) { "PASS" } else { "FAIL" })) -Detail (Limit-Detail -Text $preview.detail)

    $workerSocket = $null
    try {
        $workerSocket = Connect-Cdp -WebSocketUrl (Get-ServiceWorkerWebSocketUrl -DebugPort $debugPort -ExtensionId $extensionId)
        Invoke-Cdp -Client $workerSocket -Method "Runtime.enable" | Out-Null
        $contextMenuExpression = @"
(async () => {
  if (typeof handleContextMenuClick !== "function") {
    return { ok: false, detail: "handleContextMenuClick function missing" };
  }
  await handleContextMenuClick({
    menuItemId: "readout-speak",
    selectionText: "ReadOut extension context menu runtime smoke."
  }, { id: -1 });
  const stopped = await fetch(READOUT_URL + "/stop", { method: "POST" }).then((res) => res.json());
  return {
    ok: stopped.status === "stopped",
    detail: "selected text sent; stop=" + stopped.status
  };
})()
"@
        $contextMenu = Invoke-CdpExpression -Client $workerSocket -Expression $contextMenuExpression -AwaitPromise
        Add-Result -Check "Context menu Read aloud action" -Result ($(if ($contextMenu.ok) { "PASS" } else { "FAIL" })) -Detail (Limit-Detail -Text $contextMenu.detail)
    } finally {
        if ($workerSocket) {
            try { $workerSocket.Dispose() } catch {}
        }
    }

    $stopExpression = @"
(async () => {
  if (typeof stopPlayback !== "function") {
    return { ok: false, detail: "stopPlayback function missing" };
  }
  await stopPlayback();
  const detail = document.querySelector("#status-detail")?.textContent || "";
  return { ok: detail.includes("Stop sent to ReadOut."), detail };
})()
"@
    $stop = Invoke-CdpExpression -Client $socket -Expression $stopExpression -AwaitPromise
    Add-Result -Check "Popup Stop action" -Result ($(if ($stop.ok) { "PASS" } else { "FAIL" })) -Detail (Limit-Detail -Text $stop.detail)
} catch {
    Add-Result -Check "Extension runtime smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    if ($socket) {
        try { $socket.Dispose() } catch {}
    }
    if ($browser -and -not $browser.HasExited) {
        Stop-Process -Id $browser.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $browser.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop extension browser" -Result "PASS" -Detail "pid=$($browser.Id)"
    }
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $server.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop source server" -Result "PASS" -Detail "pid=$($server.Id)"
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

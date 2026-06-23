# Stateful non-audio smoke for the browser control panel backend.
# Backs up and restores local ReadOut config/history files.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$configDir = Join-Path $HOME ".readout"
$configPath = Join-Path $configDir "config.json"
$historyPath = Join-Path $configDir "history.json"
$configExisted = Test-Path $configPath
$historyExisted = Test-Path $historyPath
$configBackup = if ($configExisted) { [System.IO.File]::ReadAllBytes((Resolve-Path $configPath)) } else { $null }
$historyBackup = if ($historyExisted) { [System.IO.File]::ReadAllBytes((Resolve-Path $historyPath)) } else { $null }

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

function Assert-LoopbackBaseUrl {
    $uri = [uri]$BaseUrl
    if ($uri.Scheme -notin @("http", "https")) {
        throw "Unsupported BaseUrl scheme: $($uri.Scheme)"
    }

    if ($uri.Host -notin @("127.0.0.1", "localhost")) {
        throw "Refusing stateful smoke against non-loopback host: $($uri.Host)"
    }
}

function Invoke-Json {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )

    $args = @{
        Uri = "$BaseUrl$Path"
        Method = $Method
        TimeoutSec = 10
    }

    if ($null -ne $Body) {
        $args.ContentType = "application/json"
        $args.Body = ($Body | ConvertTo-Json -Compress)
    }

    Invoke-RestMethod @args
}

function Restore-File {
    param(
        [string]$Path,
        [bool]$Existed,
        [byte[]]$Backup
    )

    if ($Existed) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) *> $null
        [System.IO.File]::WriteAllBytes($Path, $Backup)
    } elseif (Test-Path $Path) {
        Remove-Item -Path $Path -Force
    }
}

try {
    Assert-LoopbackBaseUrl
    Add-Result -Check "Loopback target" -Result "PASS" -Detail $BaseUrl

    $status = Invoke-Json -Method "GET" -Path "/status"
    foreach ($required in @("status", "engine", "voice", "speed", "dependency_issues")) {
        if ($required -notin $status.PSObject.Properties.Name) {
            throw "Missing '$required' in /status response."
        }
    }
    Add-Result -Check "Status refresh backend" -Result "PASS" -Detail "status=$($status.status); engine=$($status.engine)"

    $control = Invoke-WebRequest -Uri "$BaseUrl/control" -Method Get -TimeoutSec 10
    $html = [string]$control.Content
    foreach ($needle in @(
        "Preview Voice",
        "Speak + Save WAV",
        "Remember recent reads on this device",
        "Clear History"
    )) {
        if ($html -notlike "*$needle*") {
            throw "Missing '$needle' in /control HTML."
        }
    }
    Add-Result -Check "Control panel backend page" -Result "PASS" -Detail "required controls present"

    $config = Invoke-Json -Method "PATCH" -Path "/config" -Body @{
        history_enabled = $true
        history_limit = 3
    }
    if (-not $config.config.history_enabled -or $config.config.history_limit -ne 3) {
        throw "PATCH /config did not enable history with limit=3."
    }
    Add-Result -Check "History toggle via config" -Result "PASS" -Detail "history_enabled=True; history_limit=3"

    $history = Invoke-Json -Method "GET" -Path "/history"
    if (-not $history.enabled) {
        throw "GET /history did not reflect enabled history."
    }
    Add-Result -Check "History status refresh" -Result "PASS" -Detail "enabled=$($history.enabled); rows=$($history.history.Count)"

    $cleared = Invoke-Json -Method "DELETE" -Path "/history"
    if ($cleared.status -ne "cleared") {
        throw "DELETE /history did not return cleared."
    }
    Add-Result -Check "Clear History backend" -Result "PASS" -Detail "status=$($cleared.status)"

    $stopped = Invoke-Json -Method "POST" -Path "/stop"
    if ($stopped.status -ne "stopped") {
        throw "POST /stop did not return stopped."
    }
    Add-Result -Check "Stop backend" -Result "PASS" -Detail "status=$($stopped.status)"
} catch {
    Add-Result -Check "Control workflow smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    try {
        Restore-File -Path $configPath -Existed $configExisted -Backup $configBackup
        Restore-File -Path $historyPath -Existed $historyExisted -Backup $historyBackup
        Add-Result -Check "Restore local config/history" -Result "PASS" -Detail "$configPath; $historyPath"
    } catch {
        Add-Result -Check "Restore local config/history" -Result "FAIL" -Detail $_.Exception.Message
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

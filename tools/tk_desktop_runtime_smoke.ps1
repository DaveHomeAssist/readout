# Runtime non-audio smoke for the Tk desktop UI.
# Starts a temporary source server, opens the real Tk window, verifies
# engine/voice/speed persistence and Preview/Speak/Save/Stop wiring through
# the backend, then restores local files.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [int]$TimeoutSec = 120,
    [string]$PythonExe = "python",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]
$process = $null
$stdoutLog = Join-Path $env:TEMP "readout-tk-runtime-smoke-$PID.stdout.log"
$stderrLog = Join-Path $env:TEMP "readout-tk-runtime-smoke-$PID.stderr.log"
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
        Detail = (($Detail -replace "\|", "/") -replace "\s+", " ").Trim()
    })
}

function Restore-File {
    param(
        [string]$Path,
        [bool]$Existed,
        [byte[]]$Backup
    )

    if ($Existed) {
        [System.IO.File]::WriteAllBytes($Path, $Backup)
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
        throw "Refusing Tk runtime smoke against non-loopback host: $($uri.Host)"
    }
    if ($uri.Port -ne 7778) {
        throw "Tk desktop UI currently targets localhost:7778; got port $($uri.Port)."
    }
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

function Invoke-TkSmoke {
    $env:READOUT_TK_SMOKE_BASE_URL = $BaseUrl
    $pythonSmoke = @'
import json
import os
import sys
import time
import urllib.request

import ui

BASE = os.environ["READOUT_TK_SMOKE_BASE_URL"]
results = []
pending_callbacks = []


def add(check, passed, detail):
    results.append({
        "Check": check,
        "Result": "PASS" if passed else "FAIL",
        "Detail": str(detail),
    })


def get_status():
    with urllib.request.urlopen(BASE + "/status", timeout=5) as response:
        return json.loads(response.read())


def pump(app, seconds=0.2):
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.update()
        while pending_callbacks:
            callback, args = pending_callbacks.pop(0)
            callback(*args)
        time.sleep(0.02)


def wait_status(predicate, detail, app, timeout=5):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        pump(app, 0.1)
        last = get_status()
        if predicate(last):
            return last
    raise AssertionError(f"Timed out waiting for {detail}; last={last}")


def wait_ui(predicate, detail, app, timeout=60):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        pump(app, 0.1)
        last = predicate()
        if last:
            return last
    raise AssertionError(f"Timed out waiting for {detail}; last={last}")


def patch_config(payload):
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        BASE + "/config",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read())


app = None
try:
    ui.BASE_URL = BASE
    ui.ReadOutApp._poll_status = lambda self: None
    app = ui.ReadOutApp()
    original_after = app.after

    def smoke_after(delay_ms, callback=None, *args):
        if delay_ms == 0 and callback is not None:
            pending_callbacks.append((callback, args))
            return "smoke-after"
        return original_after(delay_ms, callback, *args)

    app.after = smoke_after
    pump(app, 0.8)

    add(
        "Tk window opens",
        bool(app.winfo_ismapped()),
        f"title={app.title()}; size={app.winfo_width()}x{app.winfo_height()}; screen={app.winfo_screenwidth()}x{app.winfo_screenheight()}",
    )
    add(
        "Tk controls present",
        all(hasattr(app, name) for name in ("_engine_btns", "_voice_menu", "_preview_btn", "_save_btn", "_play_btn")),
        "engine tabs, voice menu, preview/save/play controls",
    )

    app._select_engine("openai")
    status = wait_status(lambda data: data.get("engine") == "openai" and data.get("voice") == "alloy", "engine=openai voice=alloy", app)
    add("Desktop engine persists", True, f"engine={status.get('engine')}; voice={status.get('voice')}")

    app._select_voice("nova")
    status = wait_status(lambda data: data.get("voice") == "nova", "voice=nova", app)
    add("Desktop voice persists", True, f"voice={status.get('voice')}")

    app._speed.set(1.7)
    app._on_speed_change()
    status = wait_status(lambda data: abs(float(data.get("speed", 0)) - 1.7) < 0.01, "speed=1.7", app)
    add("Desktop speed persists", True, f"speed={status.get('speed')}")

    patch_config({
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
    })
    status = wait_status(
        lambda data: data.get("engine") == "kokoro" and data.get("voice") == "af_heart",
        "engine=kokoro voice=af_heart",
        app,
        timeout=10,
    )
    app._select_engine("kokoro", persist=False, selected_voice="af_heart")
    app._speed.set(1.0)
    app._on_speed_change(persist=False)

    app._preview_voice()
    wait_ui(lambda: app._preview_btn.cget("text") == "Preview Voice", "preview completion", app)
    add(
        "Desktop Preview Voice action",
        app._status_text.get() != "ERROR",
        f"engine={status.get('engine')}; voice={status.get('voice')}; button={app._preview_btn.cget('text')}",
    )

    app._text_input.delete("1.0", "end")
    app._text_input.insert("1.0", "ReadOut Tk runtime smoke. Speak this through the desktop UI.")
    app._text_input.configure(fg=ui.C_TEXT)
    app._play()
    wait_ui(lambda: app._playing, "desktop speak playback state", app)
    pump(app, 1.0)
    add("Desktop Speak action", app._status_text.get() != "ERROR" and app._playing, f"playing={app._playing}")

    save_dir = os.path.expanduser(str(get_status().get("save_dir") or "~/Desktop/ReadOut"))
    os.makedirs(save_dir, exist_ok=True)
    before = set(os.listdir(save_dir))
    app._save_audio()
    wait_ui(lambda: app._save_btn.cget("text").startswith("✓"), "desktop save completion", app, timeout=90)
    after = set(os.listdir(save_dir))
    created = sorted(after - before)
    saved = created[0] if created else ""
    saved_path = os.path.join(save_dir, saved) if saved else ""
    saved_size = os.path.getsize(saved_path) if saved_path else 0
    add(
        "Desktop Save WAV action",
        bool(saved_path and saved_size > 44),
        f"{saved_path}; bytes={saved_size}",
    )
    if saved_path:
        try:
            os.remove(saved_path)
        except OSError:
            pass

    app._stop()
    wait_ui(lambda: not app._playing, "desktop stop playback state", app, timeout=10)
    add("Desktop Stop action", not app._playing, f"playing={app._playing}")
except Exception as exc:
    add("Tk desktop runtime smoke", False, str(exc))
finally:
    if app is not None:
        try:
            app.destroy()
        except Exception:
            pass

print(json.dumps(results))
if any(row["Result"] == "FAIL" for row in results):
    sys.exit(1)
'@

    $output = @($pythonSmoke | & $PythonExe - 2>&1)
    $exitCode = $LASTEXITCODE
    $jsonText = ($output -join "`n").Trim()
    try {
        $rows = $jsonText | ConvertFrom-Json
        foreach ($row in $rows) {
            Add-Result -Check $row.Check -Result $row.Result -Detail $row.Detail
        }
    } catch {
        Add-Result -Check "Tk desktop runtime smoke" -Result "FAIL" -Detail "Could not parse Python smoke output: $jsonText"
    }

    return $exitCode
}

try {
    Assert-LoopbackBaseUrl

    $preexisting = Test-ServerReady
    if ($preexisting.Ready) {
        throw "A server is already responding at $BaseUrl. Stop it before validating the Tk runtime workflow."
    }
    Add-Result -Check "Port available" -Result "PASS" -Detail $BaseUrl

    $process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "7778") `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog
    Add-Result -Check "Launch source server" -Result "PASS" -Detail "pid=$($process.Id)"

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ready = $false
    $readyDetail = "timeout"
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) {
            throw "Source server exited before ready. exit=$($process.ExitCode)"
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

    $smokeExit = Invoke-TkSmoke
    if ($smokeExit -ne 0) {
        Add-Result -Check "Tk desktop runtime smoke exit" -Result "FAIL" -Detail "python exit=$smokeExit"
    }
} catch {
    Add-Result -Check "Tk desktop runtime smoke" -Result "FAIL" -Detail $_.Exception.Message
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
        Add-Result -Check "Stop source server" -Result "PASS" -Detail "pid=$($process.Id)"
    }

    try {
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }
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

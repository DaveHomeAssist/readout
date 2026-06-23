# Static release smoke for the Tk desktop contract.
# This does not launch a GUI or prove audible playback.

param(
    [string]$UiPath = "ui.py",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]

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

function Add-Assert {
    param(
        [string]$Check,
        [bool]$Passed,
        [string]$PassDetail,
        [string]$FailDetail
    )

    Add-Result -Check $Check -Result ($(if ($Passed) { "PASS" } else { "FAIL" })) -Detail ($(if ($Passed) { $PassDetail } else { $FailDetail }))
}

function Read-TextFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Missing required Tk desktop file: $Path"
    }

    Get-Content -Path $Path -Raw
}

try {
    $ui = Read-TextFile -Path $UiPath

    Add-Assert -Check "Tk app class" -Passed ($ui.Contains("class ReadOutApp(tk.Tk):")) -PassDetail "ReadOutApp extends tk.Tk" -FailDetail "ReadOutApp Tk class missing"
    Add-Assert -Check "Server base URL" -Passed ($ui.Contains('BASE_URL   = f"http://localhost:{PORT}"')) -PassDetail "localhost base URL" -FailDetail "desktop must target localhost server"

    foreach ($engine in @('"kokoro":', '"openai":', '"elevenlabs":')) {
        Add-Assert -Check "Supported engine: $engine" -Passed ($ui.Contains($engine)) -PassDetail "present" -FailDetail "missing"
    }
    Add-Assert -Check "Unsupported browser engine absent" -Passed (-not $ui.Contains('"browser":')) -PassDetail "browser engine absent" -FailDetail "browser engine tab should not return"

    foreach ($needle in @(
        'self._voice_menu = tk.OptionMenu',
        'text="Preview Voice"',
        'command=self._preview_voice',
        'text="⬇  Save WAV"',
        'command=self._save_audio',
        'command=self._toggle_play',
        'RECENT / QUEUE'
    )) {
        Add-Assert -Check "Desktop control: $needle" -Passed ($ui.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    foreach ($needle in @(
        '_patch("/config", payload)',
        'payload = {"engine": key}',
        'payload["voice"] = voice_id',
        'self._patch_config({"voice": voice_id})',
        'self._patch_config({"speed": v})'
    )) {
        Add-Assert -Check "Config persistence: $needle" -Passed ($ui.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    foreach ($needle in @(
        '_get("/voices")',
        '_get("/status")',
        '_post("/preview"',
        '_post("/speak"',
        '_post("/stop")'
    )) {
        Add-Assert -Check "Endpoint wiring: $needle" -Passed ($ui.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    Add-Assert -Check "Endpoint wiring: save true payload" -Passed ($ui -match '"save"\s*:\s*True') -PassDetail "save=True speak payload" -FailDetail "save=True speak payload missing"
    Add-Assert -Check "Save MP3 copy absent" -Passed (-not $ui.Contains("Save MP3")) -PassDetail "Save MP3 absent" -FailDetail "stale Save MP3 copy found"
    Add-Assert -Check "Auto-read control absent" -Passed (-not $ui.Contains("Auto-read")) -PassDetail "Auto-read absent" -FailDetail "Auto-read control should not return"
} catch {
    Add-Result -Check "Tk desktop static smoke" -Result "FAIL" -Detail $_.Exception.Message
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

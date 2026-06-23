# Static release smoke for the Chrome extension contract.
# This does not launch Chrome or prove audible playback.

param(
    [string]$ExtensionDir = "extension",
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
        throw "Missing required extension file: $Path"
    }

    Get-Content -Path $Path -Raw
}

try {
    $manifestPath = Join-Path $ExtensionDir "manifest.json"
    $popupHtmlPath = Join-Path $ExtensionDir "popup.html"
    $popupJsPath = Join-Path $ExtensionDir "popup.js"
    $backgroundPath = Join-Path $ExtensionDir "background.js"
    $contentPath = Join-Path $ExtensionDir "content.js"

    $manifest = (Read-TextFile -Path $manifestPath) | ConvertFrom-Json
    $popupHtml = Read-TextFile -Path $popupHtmlPath
    $popupJs = Read-TextFile -Path $popupJsPath
    $backgroundJs = Read-TextFile -Path $backgroundPath
    $contentJs = Read-TextFile -Path $contentPath

    Add-Assert -Check "Manifest version" -Passed ($manifest.manifest_version -eq 3) -PassDetail "manifest_version=3" -FailDetail "manifest_version must be 3"

    $permissions = @($manifest.permissions)
    foreach ($permission in @("contextMenus", "activeTab", "scripting")) {
        Add-Assert -Check "Permission: $permission" -Passed ($permission -in $permissions) -PassDetail "present" -FailDetail "missing"
    }
    Add-Assert -Check "Least privilege: no storage permission" -Passed ("storage" -notin $permissions) -PassDetail "storage absent" -FailDetail "storage permission should not be present"

    $hostPermissions = @($manifest.host_permissions)
    Add-Assert -Check "Host permission" -Passed (($hostPermissions.Count -eq 1) -and ($hostPermissions[0] -eq "http://localhost:7778/*")) -PassDetail "http://localhost:7778/*" -FailDetail ("unexpected host permissions: " + ($hostPermissions -join ", "))

    Add-Assert -Check "Service worker" -Passed ($manifest.background.service_worker -eq "background.js") -PassDetail "background.js" -FailDetail "service worker must be background.js"
    Add-Assert -Check "Default popup" -Passed ($manifest.action.default_popup -eq "popup.html") -PassDetail "popup.html" -FailDetail "default popup must be popup.html"

    foreach ($icon in @("icon48.png", "icon128.png")) {
        Add-Assert -Check "Icon exists: $icon" -Passed (Test-Path (Join-Path $ExtensionDir $icon)) -PassDetail $icon -FailDetail "missing"
    }

    foreach ($needle in @(
        'id="status-detail"',
        'role="status"',
        'id="btn-stop"',
        'id="btn-preview"',
        'id="btn-speak"',
        'Read Selection',
        'Preview',
        'OFFLINE'
    )) {
        Add-Assert -Check "Popup HTML: $needle" -Passed ($popupHtml.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    foreach ($needle in @(
        'const READOUT_URL = "http://localhost:7778"',
        '`${READOUT_URL}/status`',
        '`${READOUT_URL}/voices`',
        '`${READOUT_URL}/preview`',
        '`${READOUT_URL}/speak`',
        '`${READOUT_URL}/stop`',
        '`${READOUT_URL}/config`',
        'check the extension origin allowlist',
        'Server offline. Start the ReadOut desktop app',
        'Dependency issue:',
        'Previewing...'
    )) {
        Add-Assert -Check "Popup JS: $needle" -Passed ($popupJs.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    foreach ($needle in @(
        'const READOUT_URL = "http://localhost:7778"',
        'readout-speak',
        'readout-speak-save',
        'readout-stop',
        'Read aloud',
        'Read aloud & save WAV',
        'Stop reading',
        '`${READOUT_URL}/speak`',
        '`${READOUT_URL}/stop`',
        'ReadOut not running. Start the desktop app.'
    )) {
        Add-Assert -Check "Background JS: $needle" -Passed ($backgroundJs.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }

    foreach ($needle in @(
        'readout-ping',
        'readout-toast',
        'readout-toast',
        'document.body.appendChild(toast)',
        'toast.remove()'
    )) {
        Add-Assert -Check "Content JS: $needle" -Passed ($contentJs.Contains($needle)) -PassDetail "present" -FailDetail "missing"
    }
} catch {
    Add-Result -Check "Extension static smoke" -Result "FAIL" -Detail $_.Exception.Message
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

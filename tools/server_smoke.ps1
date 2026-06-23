# Run from any shell after starting ReadOut.
# Non-audio smoke test for the local API and browser control surface.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [switch]$IncludeAudio
)

$ErrorActionPreference = "Stop"

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Check,
        [bool]$Passed,
        [string]$Detail
    )

    $results.Add([pscustomobject]@{
        Check = $Check
        Result = if ($Passed) { "PASS" } else { "FAIL" }
        Detail = $Detail
    })
}

function Test-JsonEndpoint {
    param(
        [string]$Check,
        [string]$Path,
        [scriptblock]$Validate
    )

    try {
        $data = Invoke-RestMethod -Uri "$BaseUrl$Path" -Method Get -TimeoutSec 5
        $detail = & $Validate $data
        Add-Result -Check $Check -Passed $true -Detail $detail
    } catch {
        Add-Result -Check $Check -Passed $false -Detail $_.Exception.Message
    }
}

Test-JsonEndpoint -Check "GET /status" -Path "/status" -Validate {
    param($data)

    $props = $data.PSObject.Properties.Name
    foreach ($required in @("status", "engine", "voice", "speed", "dependency_issues")) {
        if ($required -notin $props) {
            throw "Missing '$required' in /status response."
        }
    }

    "status=$($data.status); engine=$($data.engine); dependency_issues=$($data.dependency_issues.Count)"
}

Test-JsonEndpoint -Check "GET /voices" -Path "/voices" -Validate {
    param($data)

    if (-not $data.voices -or $data.voices.Count -lt 1) {
        throw "No voices returned."
    }

    $first = $data.voices[0]
    $props = $first.PSObject.Properties.Name
    if ("id" -notin $props -or "label" -notin $props) {
        throw "Voice rows must include id and label."
    }

    "voices=$($data.voices.Count)"
}

Test-JsonEndpoint -Check "GET /history" -Path "/history" -Validate {
    param($data)

    $props = $data.PSObject.Properties.Name
    if ("enabled" -notin $props -or "history" -notin $props) {
        throw "History response must include enabled and history."
    }

    "enabled=$($data.enabled); rows=$($data.history.Count)"
}

try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/control" -Method Get -TimeoutSec 5
    $html = [string]$response.Content
    foreach ($needle in @(
        "primary macOS control surface",
        "Preview Voice",
        "Speak + Save WAV",
        "Remember recent reads on this device",
        "Clear History"
    )) {
        if ($html -notlike "*$needle*") {
            throw "Missing '$needle' in /control HTML."
        }
    }
    Add-Result -Check "GET /control" -Passed $true -Detail "required controls present"
} catch {
    Add-Result -Check "GET /control" -Passed $false -Detail $_.Exception.Message
}

if ($IncludeAudio) {
    try {
        $body = @{ voice = "af_heart"; speed = 1.0 } | ConvertTo-Json -Compress
        $preview = Invoke-RestMethod `
            -Uri "$BaseUrl/preview" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 30
        Add-Result -Check "POST /preview" -Passed ($preview.preview -eq $true) -Detail "status=$($preview.status)"
    } catch {
        Add-Result -Check "POST /preview" -Passed $false -Detail $_.Exception.Message
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

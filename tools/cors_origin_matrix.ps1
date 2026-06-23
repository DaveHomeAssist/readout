# Run from the readout project root after starting ReadOut.
# Prints and verifies the Phase 0 CORS/Origin proof matrix.

param(
    [string]$BaseUrl = "http://127.0.0.1:7778",
    [string]$AllowedOrigin = "http://localhost:7778",
    [string]$BlockedOrigin = "https://evil.com",
    [string]$AllowedExtensionOrigin = ""
)

$ErrorActionPreference = "Stop"

function Get-HeaderValue {
    param(
        [string]$Text,
        [string]$HeaderName
    )

    $pattern = "(?i)^$([regex]::Escape($HeaderName)):\s*(.+)$"
    $match = $Text -split "`r?`n" | Where-Object { $_ -match $pattern } | Select-Object -Last 1
    if (-not $match) {
        return "<none>"
    }

    return ($match -replace $pattern, '$1').Trim()
}

function Invoke-MatrixRequest {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [hashtable]$Headers = @{},
        [string]$Body = "",
        [int]$ExpectedStatus,
        [string]$ExpectedAllowOrigin
    )

    $headerArgs = @()
    foreach ($key in $Headers.Keys) {
        $headerArgs += @("-H", "${key}: $($Headers[$key])")
    }

    $bodyArgs = @()
    if ($Body) {
        $bodyArgs = @("-H", "Content-Type: application/json", "--data", $Body)
    }

    $curlArgs = @("-sS", "-i", "-X", $Method) + $headerArgs + $bodyArgs + @("$BaseUrl$Path")
    $response = & curl.exe @curlArgs
    $text = $response -join "`n"
    $statusLine = $text -split "`r?`n" | Where-Object { $_ -match "^HTTP/" } | Select-Object -Last 1

    if (-not $statusLine) {
        throw "No HTTP status line returned for $Name. Is ReadOut running at $BaseUrl?"
    }

    $status = [int]($statusLine -replace "^HTTP/\S+\s+(\d+).*$", '$1')
    $allowOrigin = Get-HeaderValue -Text $text -HeaderName "Access-Control-Allow-Origin"
    $pass = ($status -eq $ExpectedStatus -and $allowOrigin -eq $ExpectedAllowOrigin)

    [pscustomobject]@{
        Case = $Name
        Method = $Method
        Path = $Path
        ExpectedStatus = $ExpectedStatus
        ActualStatus = $status
        ExpectedAllowOrigin = $ExpectedAllowOrigin
        ActualAllowOrigin = $allowOrigin
        Result = if ($pass) { "PASS" } else { "FAIL" }
    }
}

$cases = @(
    @{
        Name = "no-origin status"
        Method = "GET"
        Path = "/status"
        Headers = @{}
        Body = ""
        ExpectedStatus = 200
        ExpectedAllowOrigin = "<none>"
    },
    @{
        Name = "allowed local status"
        Method = "GET"
        Path = "/status"
        Headers = @{ Origin = $AllowedOrigin }
        Body = ""
        ExpectedStatus = 200
        ExpectedAllowOrigin = $AllowedOrigin
    },
    @{
        Name = "allowed local config preflight"
        Method = "OPTIONS"
        Path = "/config"
        Headers = @{
            Origin = $AllowedOrigin
            "Access-Control-Request-Method" = "PATCH"
            "Access-Control-Request-Headers" = "content-type"
        }
        Body = ""
        ExpectedStatus = 204
        ExpectedAllowOrigin = $AllowedOrigin
    },
    @{
        Name = "blocked evil status"
        Method = "GET"
        Path = "/status"
        Headers = @{ Origin = $BlockedOrigin }
        Body = ""
        ExpectedStatus = 403
        ExpectedAllowOrigin = "<none>"
    },
    @{
        Name = "blocked evil stop"
        Method = "POST"
        Path = "/stop"
        Headers = @{ Origin = $BlockedOrigin }
        Body = ""
        ExpectedStatus = 403
        ExpectedAllowOrigin = "<none>"
    }
)

if ($AllowedExtensionOrigin) {
    $cases += @{
        Name = "allowed extension config preflight"
        Method = "OPTIONS"
        Path = "/config"
        Headers = @{
            Origin = $AllowedExtensionOrigin
            "Access-Control-Request-Method" = "PATCH"
            "Access-Control-Request-Headers" = "content-type"
        }
        Body = ""
        ExpectedStatus = 204
        ExpectedAllowOrigin = $AllowedExtensionOrigin
    }
}

$results = foreach ($case in $cases) {
    Invoke-MatrixRequest @case
}

Write-Host "| Case | HTTP | Access-Control-Allow-Origin | Result |"
Write-Host "|---|---:|---|---|"
foreach ($row in $results) {
    Write-Host "| $($row.Case) | $($row.ActualStatus) | $($row.ActualAllowOrigin) | $($row.Result) |"
}

if ($results.Result -contains "FAIL") {
    exit 1
}

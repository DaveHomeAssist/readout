# Lightweight release secret scan.
# Fails on common provider-token shapes or committed non-empty provider keys.

param(
    [string]$Root = ".",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$excludedDirs = @(
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "build",
    "dist"
)

$includedExtensions = @(
    ".py",
    ".ps1",
    ".sh",
    ".md",
    ".json",
    ".html",
    ".js",
    ".txt",
    ".spec"
)

$patterns = @(
    @{
        Name = "OpenAI API key literal"
        Regex = "sk-[A-Za-z0-9_-]{20,}"
    },
    @{
        Name = "ElevenLabs API key literal"
        Regex = "sk_[A-Za-z0-9]{20,}"
    },
    @{
        Name = "Committed provider key value"
        Regex = '["''](?:openai_api_key|elevenlabs_api_key)["'']\s*:\s*["''](?!\*{3}|["''])[^"'']{20,}["'']'
    }
)

function Is-ExcludedPath {
    param([string]$Path)

    foreach ($dir in $excludedDirs) {
        if ($Path -match "(^|[\\/])$([regex]::Escape($dir))([\\/]|$)") {
            return $true
        }
    }

    return $false
}

$rootPath = (Resolve-Path $Root).Path
$findings = New-Object System.Collections.Generic.List[object]

Get-ChildItem -Path $rootPath -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    $path = $_.FullName
    if (Is-ExcludedPath -Path $path) {
        return
    }

    if ($includedExtensions -notcontains $_.Extension) {
        return
    }

    $relative = [System.IO.Path]::GetRelativePath($rootPath, $path)
    $lineNo = 0
    Get-Content -LiteralPath $path | ForEach-Object {
        $lineNo += 1
        $line = $_
        foreach ($pattern in $patterns) {
            if ($line -match $pattern.Regex) {
                $findings.Add([pscustomobject]@{
                    File = $relative
                    Line = $lineNo
                    Pattern = $pattern.Name
                })
            }
        }
    }
}

if ($findings.Count -eq 0) {
    if (-not $Quiet) {
        Write-Host "| Check | Result | Detail |"
        Write-Host "|---|---|---|"
        Write-Host "| Secret scan | PASS | No provider key literals found |"
    }
    exit 0
}

if (-not $Quiet) {
    Write-Host "| File | Line | Pattern |"
    Write-Host "|---|---:|---|"
    foreach ($finding in $findings) {
        Write-Host "| $($finding.File) | $($finding.Line) | $($finding.Pattern) |"
    }
}

exit 1

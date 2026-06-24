# build_windows.ps1 — Build ReadOut.exe for Windows
# Run from the readout\ project root in PowerShell.
# Requires: Python 3.10-3.12 and an eSpeak NG runtime.

$ErrorActionPreference = "Stop"

Write-Host "── ReadOut Windows Build ──────────────────────────────────" -ForegroundColor Cyan

# 1. Resolve a supported Python interpreter without trusting the WindowsApps shim
function Test-CommandAvailable {
    param([string]$Exe)

    if ($Exe -match "[\\/]") {
        return Test-Path $Exe
    }

    return [bool](Get-Command $Exe -ErrorAction SilentlyContinue)
}

function Test-SupportedPython {
    param(
        [string]$Exe,
        [string[]]$BaseArgs = @()
    )

    $check = "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 13) else 1)"
    try {
        $argv = @($BaseArgs + @("-c", $check))
        & $Exe @argv *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-PythonVersionText {
    param(
        [string]$Exe,
        [string[]]$BaseArgs = @()
    )

    try {
        $argv = @($BaseArgs + @("--version"))
        return (& $Exe @argv 2>&1 | Select-Object -First 1)
    } catch {
        return "version unavailable"
    }
}

function Test-EspeakRuntime {
    param(
        [string]$Exe,
        [string[]]$BaseArgs = @()
    )

    $espeak = Get-Command espeak-ng -ErrorAction SilentlyContinue
    if ($espeak) {
        return [pscustomobject]@{
            Ok = $true
            Detail = "system espeak-ng on PATH: $($espeak.Source)"
        }
    }

    $check = @"
import espeakng_loader
espeakng_loader.make_library_available()
print("bundled espeakng_loader")
"@
    try {
        $argv = @($BaseArgs + @("-c", $check))
        $output = @(& $Exe @argv 2>&1)
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{
                Ok = $true
                Detail = (($output | Select-Object -First 1) -join "")
            }
        }
        return [pscustomobject]@{
            Ok = $false
            Detail = (($output -join " ") -replace "\s+", " ").Trim()
        }
    } catch {
        return [pscustomobject]@{
            Ok = $false
            Detail = $_.Exception.Message
        }
    }
}

$pythonCandidates = @(
    @{ Label = "existing .venv"; Exe = ".\.venv\Scripts\python.exe"; Args = @() },
    @{ Label = "Python Launcher 3.12"; Exe = "py"; Args = @("-3.12") },
    @{ Label = "Python Launcher 3.11"; Exe = "py"; Args = @("-3.11") },
    @{ Label = "Python Launcher 3.10"; Exe = "py"; Args = @("-3.10") },
    @{ Label = "python on PATH"; Exe = "python"; Args = @() }
)

$PythonExe = $null
$PythonArgs = @()
$PythonLabel = $null

foreach ($candidate in $pythonCandidates) {
    if (-not (Test-CommandAvailable $candidate.Exe)) {
        continue
    }

    if (Test-SupportedPython -Exe $candidate.Exe -BaseArgs $candidate.Args) {
        $PythonExe = $candidate.Exe
        $PythonArgs = $candidate.Args
        $PythonLabel = $candidate.Label
        break
    }
}

if (-not $PythonExe) {
    Write-Host ""
    Write-Host "ERROR: Python 3.10-3.12 is required for Kokoro." -ForegroundColor Red
    Write-Host "Install Python 3.12, 3.11, or 3.10, then retry."
    Write-Host "Recommended check: py -3.12 --version"
    exit 1
}

$pyver = Get-PythonVersionText -Exe $PythonExe -BaseArgs $PythonArgs
Write-Host "Python: $pyver ($PythonLabel)"

# 2. Create / activate venv
if (-not (Test-Path ".venv")) {
    Write-Host "Creating venv..."
    $venvArgs = @($PythonArgs + @("-m", "venv", ".venv"))
    & $PythonExe @venvArgs
}
& .\.venv\Scripts\Activate.ps1
$VenvPython = ".\.venv\Scripts\python.exe"

if (-not (Test-SupportedPython -Exe $VenvPython)) {
    Write-Host ""
    Write-Host "ERROR: Existing .venv is not Python 3.10-3.12." -ForegroundColor Red
    Write-Host "Remove .venv after saving any local work, recreate it with a supported Python, and retry."
    exit 1
}

# 3. Install dependencies
Write-Host "Installing dependencies..."
& $VenvPython -m pip install --upgrade pip -q
& $VenvPython -m pip install -r requirements.txt -q

# 4. Verify eSpeak NG runtime after requirements are installed
$espeakRuntime = Test-EspeakRuntime -Exe $VenvPython
if (-not $espeakRuntime.Ok) {
    Write-Host ""
    Write-Host "ERROR: eSpeak NG runtime unavailable." -ForegroundColor Red
    Write-Host "Expected system espeak-ng on PATH or bundled espeakng_loader from requirements.txt."
    Write-Host "Detail: $($espeakRuntime.Detail)"
    exit 1
}
Write-Host "espeak-ng: OK ($($espeakRuntime.Detail))"

# 5. Generate placeholder icon if missing
if (-not (Test-Path "assets\icon.ico")) {
    Write-Host "Generating Windows icon..."
    & $VenvPython -c @"
from PIL import Image, ImageDraw
import os
os.makedirs('assets', exist_ok=True)
png_path = r'assets\icon.png'
if os.path.exists(png_path):
    img = Image.open(png_path).convert('RGBA')
else:
    img = Image.new('RGBA', (256, 256), (14, 14, 14, 255))
    d = ImageDraw.Draw(img)
    cx, cy = 128, 128
    for i, h in enumerate([20, 40, 65, 85, 65, 40, 20]):
        x = cx - 3*21 + i*21
        d.rectangle([x, cy-h, x+14, cy+h], fill=(184, 245, 66, 255))
    img.save(png_path)
sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
imgs  = [img.resize(s) for s in sizes]
imgs[0].save('assets\icon.ico', format='ICO', sizes=sizes,
             append_images=imgs[1:])
print('icon.ico generated.')
"@
}

# 6. Clean previous build
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist"  }

# 7. PyInstaller
Write-Host "Running PyInstaller..."
& $VenvPython -m PyInstaller ReadOut.spec

# 8. Verify
if (Test-Path "dist\ReadOut\ReadOut.exe") {
    Write-Host ""
    Write-Host "Build complete: dist\ReadOut\ReadOut.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run:    .\dist\ReadOut\ReadOut.exe"
    Write-Host "To install: Copy dist\ReadOut\ to %APPDATA%\ReadOut\"
    Write-Host ""
    Write-Host "To add to Windows startup (run in PowerShell as admin):"
    Write-Host '  $exe = "$env:APPDATA\ReadOut\ReadOut.exe"'
    Write-Host '  $reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"'
    Write-Host '  Set-ItemProperty -Path $reg -Name "ReadOut" -Value $exe'
} else {
    Write-Host "Build failed — check output above." -ForegroundColor Red
    exit 1
}

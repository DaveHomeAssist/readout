# build_windows.ps1 — Build ReadOut.exe for Windows
# Run from the readout\ project root in PowerShell.
# Requires: Python 3.10-3.12, espeak-ng MSI installed first.

$ErrorActionPreference = "Stop"

Write-Host "── ReadOut Windows Build ──────────────────────────────────" -ForegroundColor Cyan

# 1. Check Python version
$pyver = python --version 2>&1
Write-Host "Python: $pyver"

# 2. Check espeak-ng is on PATH
if (-not (Get-Command espeak-ng -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "ERROR: espeak-ng not found on PATH." -ForegroundColor Red
    Write-Host "Download from: https://github.com/espeak-ng/espeak-ng/releases"
    Write-Host "Install the .msi and ensure it is added to PATH."
    exit 1
}
Write-Host "espeak-ng: OK"

# 3. Create / activate venv
if (-not (Test-Path ".venv")) {
    Write-Host "Creating venv..."
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1

# 4. Install dependencies
Write-Host "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 5. Generate placeholder icon if missing
if (-not (Test-Path "assets\icon.ico")) {
    Write-Host "Generating placeholder icon..."
    python -c @"
from PIL import Image, ImageDraw
import os
os.makedirs('assets', exist_ok=True)
img = Image.new('RGBA', (256, 256), (14, 14, 14, 255))
d   = ImageDraw.Draw(img)
cx, cy = 128, 128
for i, h in enumerate([20, 40, 65, 85, 65, 40, 20]):
    x = cx - 3*21 + i*21
    d.rectangle([x, cy-h, x+14, cy+h], fill=(184, 245, 66, 255))
img.save('assets\icon.png')
# Save as multi-size ICO
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
pyinstaller ReadOut.spec

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

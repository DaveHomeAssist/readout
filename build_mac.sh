#!/usr/bin/env bash
# build_mac.sh — Build ReadOut.app for macOS (M1/M2/M3/M4)
# Run from the readout/ project root.
set -euo pipefail

echo "── ReadOut macOS Build ──────────────────────────────────"

# 1. Ensure we're on Python 3.10–3.12
PY=$(python3 --version 2>&1)
echo "Python: $PY"

# 2. Create / activate venv
if [ ! -d ".venv" ]; then
  echo "Creating venv..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Install deps
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Install espeak-ng via Homebrew (required by kokoro/misaki)
if ! command -v espeak-ng &>/dev/null; then
  echo "Installing espeak-ng via Homebrew..."
  brew install espeak-ng
else
  echo "espeak-ng already installed."
fi

# 5. Set MPS fallback for M-series chips
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 6. Generate placeholder icon if not present
if [ ! -f "assets/icon.icns" ]; then
  echo "Generating placeholder icon..."
  python3 - <<'PYEOF'
from PIL import Image, ImageDraw
import os
os.makedirs("assets", exist_ok=True)
img = Image.new("RGBA", (512, 512), (14, 14, 14, 255))
d   = ImageDraw.Draw(img)
cx, cy = 256, 256
for i, h in enumerate([40, 80, 130, 170, 130, 80, 40]):
    x = cx - 3*42 + i*42
    d.rectangle([x, cy-h, x+28, cy+h], fill=(184, 245, 66, 255))
img.save("assets/icon.png")
# Naive icns via iconutil (requires macOS)
import subprocess, shutil
icon_dir = "assets/ReadOut.iconset"
os.makedirs(icon_dir, exist_ok=True)
for sz in [16,32,64,128,256,512]:
    img.resize((sz,sz)).save(f"{icon_dir}/icon_{sz}x{sz}.png")
    img.resize((sz*2,sz*2)).save(f"{icon_dir}/icon_{sz}x{sz}@2x.png")
subprocess.run(["iconutil", "-c", "icns", icon_dir,
                "-o", "assets/icon.icns"], check=True)
shutil.rmtree(icon_dir)
print("icon.icns generated.")
PYEOF
fi

# 7. Clean previous build
rm -rf build dist

# 8. PyInstaller
echo "Running PyInstaller..."
pyinstaller ReadOut.spec

# 9. Verify
if [ -d "dist/ReadOut.app" ]; then
  echo ""
  echo "✅  Build complete: dist/ReadOut.app"
  echo "    Size: $(du -sh dist/ReadOut.app | cut -f1)"
  echo ""
  echo "To run:         open dist/ReadOut.app"
  echo "To install:     cp -r dist/ReadOut.app /Applications/"
  echo "To add to login items: System Settings → General → Login Items"
else
  echo "❌  Build failed — check output above."
  exit 1
fi

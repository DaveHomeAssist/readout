#!/usr/bin/env bash
# build_mac.sh — Build ReadOut.app for macOS (M1/M2/M3/M4)
# Run from the readout/ project root.
set -euo pipefail

echo "── ReadOut macOS Build ──────────────────────────────────"

# 1. Resolve a supported Python interpreter (3.10–3.12)
PYTHON_BIN=""

is_supported_python() {
  "$1" - <<'PYEOF' >/dev/null 2>&1
import sys
raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 13) else 1)
PYEOF
}

for candidate in \
  ".venv/bin/python" \
  "/opt/homebrew/opt/python@3.12/bin/python3.12" \
  "python3.12" \
  "python3.11" \
  "python3.10" \
  "python3"
do
  if [ -x "$candidate" ]; then
    resolved="$candidate"
  elif command -v "$candidate" >/dev/null 2>&1; then
    resolved="$(command -v "$candidate")"
  else
    continue
  fi

  if is_supported_python "$resolved"; then
    PYTHON_BIN="$resolved"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "❌  Python 3.10–3.12 required. Install python@3.12 and retry."
  exit 1
fi

PY="$("$PYTHON_BIN" --version 2>&1)"
echo "Python: $PY"

# 2. Check espeak-ng is on PATH
if ! command -v espeak-ng >/dev/null 2>&1; then
  echo "❌  espeak-ng not found on PATH."
  echo "    Install with: brew install espeak-ng"
  exit 1
fi
echo "espeak-ng: OK"

# 3. Create / activate venv
if [ ! -d ".venv" ]; then
  echo "Creating venv..."
  "$PYTHON_BIN" -m venv .venv
fi
source .venv/bin/activate

if ! is_supported_python ".venv/bin/python"; then
  echo "❌  Existing .venv is not Python 3.10–3.12."
  echo "    Remove .venv after saving any local work, recreate it with a supported Python, and retry."
  exit 1
fi

# 4. Install deps
echo "Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r requirements.txt -q

# 5. Set MPS fallback for M-series chips
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 6. Generate placeholder icon if not present
if [ ! -f "assets/icon.icns" ]; then
  echo "Generating placeholder icon..."
  .venv/bin/python - <<'PYEOF'
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
echo "Running PyInstaller (macOS app mode: tray + control panel, no Tk window)..."
.venv/bin/python -m PyInstaller ReadOut.spec

# 9. Verify
if [ -d "dist/ReadOut.app" ]; then
  echo ""
  echo "✅  Build complete: dist/ReadOut.app"
  echo "    Size: $(du -sh dist/ReadOut.app | cut -f1)"
  echo ""
  echo "To run:         open dist/ReadOut.app"
  echo "To install:     cp -r dist/ReadOut.app /Applications/"
  echo "To add to login items: System Settings → General → Login Items"
  echo "Control panel:  Use the tray icon → Open Control Panel"
else
  echo "❌  Build failed — check output above."
  exit 1
fi

# ReadOut — Desktop TTS

Private by default text-to-speech desktop app.
Kokoro 82M model runs entirely on your machine — no API costs, no data leaves when Kokoro is selected.
FastAPI local server on `localhost:7778` accepts calls from the browser extension.

---

## Prerequisites

### macOS (M4 MacBook Air)
```bash
brew install espeak-ng
# Python 3.10–3.12 required (NOT 3.13)
python3 --version
```

### Windows (Duncan)
1. Download `espeak-ng-*.msi` from https://github.com/espeak-ng/espeak-ng/releases
2. Run installer — make sure "Add to PATH" is checked
3. Verify: `espeak-ng --version` in PowerShell

---

## Development (run from source)

```bash
# 1. Clone / cd into readout/
cd readout

# 2. Create venv (Python 3.10–3.12)
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .\.venv\Scripts\Activate.ps1    # Windows

# 3. Install deps
pip install -r requirements.txt

# 4. macOS M-series only — enable Metal GPU acceleration
export PYTORCH_ENABLE_MPS_FALLBACK=1   # add to ~/.zshrc permanently

# 5. Run the tray app + local control panel
python main.py
```

For API-only development without the tray or auto-opened control panel:

```bash
python main.py --headless --no-browser
```

Then open `http://127.0.0.1:7778/control`.

First launch downloads the Kokoro model weights (~300 MB) from Hugging Face.  
A tray notification shows progress. Subsequent launches are instant.

---

## Build standalone executable

### macOS → ReadOut.app
```bash
chmod +x build_mac.sh
./build_mac.sh
# Output: dist/ReadOut.app
open dist/ReadOut.app
```

The packaged macOS app runs as a menu-bar app and does not use the Tk desktop
window. Open the control panel from the tray icon via `Open Control Panel`.

To install permanently:
```bash
cp -r dist/ReadOut.app /Applications/
# Add to Login Items: System Settings → General → Login Items → +
```

### Windows → ReadOut.exe
```powershell
# In PowerShell (not cmd)
.\build_windows.ps1
# Output: dist\ReadOut\ReadOut.exe
```

To add to Windows startup:
```powershell
$exe = "$env:APPDATA\ReadOut\ReadOut.exe"
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $reg -Name "ReadOut" -Value $exe
```

---

## Project structure

```
readout/
├── main.py          Entry point — tray + server + /control orchestration
├── main_app.py      Packaged macOS entry point
├── server.py        FastAPI REST API  (localhost:7778)
├── tts_engine.py    Kokoro wrapper + playback + save
├── config.py        ~/.readout/config.json manager
├── extension/       Chrome MV3 extension + design reference
├── assets/
│   ├── icon.png     64×64 tray icon
│   ├── icon.icns    macOS app icon (auto-generated)
│   └── icon.ico     Windows app icon (auto-generated)
├── requirements.txt
├── ReadOut.spec     PyInstaller spec (both platforms)
├── build_mac.sh     macOS build script
└── build_windows.ps1 Windows build script
```

---

## API endpoints (localhost:7778)

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | /speak | `{text, voice?, speed?, save?}` | Speak text |
| POST | /stop | — | Stop playback |
| GET | /status | — | Health + current config |
| GET | /voices | — | Voice and engine catalogue |
| PATCH | /config | `{voice?, speed?, engine?, ...}` | Update settings; rejects unsupported engines |

---

## Config file (~/.readout/config.json)

```json
{
  "voice":              "af_heart",
  "speed":              1.0,
  "lang_code":          "a",
  "always_save":        false,
  "save_dir":           "~/Desktop/ReadOut",
  "port":               7778,
  "engine":             "kokoro",
  "openai_api_key":     "",
  "elevenlabs_api_key": ""
}
```

Edited live — no restart required.

---

## Voice reference (Kokoro v1.0)

| ID | Description |
|----|-------------|
| `af_heart` | American female, warm — default |
| `af_sky` | American female, bright |
| `am_adam` | American male, deep |
| `am_echo` | American male, casual |
| `bf_emma` | British female, clear |
| `bm_lewis` | British male, conversational |

Voice blending: pass `"af_heart:60,am_adam:40"` as the voice parameter.

---

## Port note

Port `7777` is reserved for DaveLLM Router (PLB).  
ReadOut uses `7778` by default. Both can run simultaneously.

---

## Browser extension

See `extension/` directory (separate). The extension right-click menu posts  
selected page text to `http://localhost:7778/speak` — ReadOut plays it instantly.

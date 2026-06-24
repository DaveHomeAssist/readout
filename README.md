# ReadOut — Desktop TTS

Local-first text-to-speech desktop app.
Kokoro 82M model runs entirely on your machine — no API costs, no data leaves.
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
1. Install Python 3.10, 3.11, or 3.12. Kokoro is not supported on Python 3.13.
2. Verify a supported interpreter is registered: `py -3.12 --version` or `py -3.11 --version`
3. Install dependencies in the project venv: `python -m pip install -r requirements.txt`
4. The venv-provided `espeakng-loader` satisfies Kokoro's eSpeak runtime. A
   system `espeak-ng` MSI on PATH is still supported, but it is not required
   when `espeakng-loader` is importable.

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

# 5. Run
python main.py --headless --no-browser
```

On macOS, the browser control panel is the primary UI. Run:

```bash
python main.py --headless --no-browser
```

That starts the local API without using Tk. Then open:
`http://127.0.0.1:7778/control`

The Tk desktop window remains available for troubleshooting with
`READOUT_FORCE_TK=1`, but it is not the primary macOS workflow.

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

The build script fails before packaging unless Python 3.10-3.12 and an eSpeak
NG runtime are available. The runtime can be system `espeak-ng` or the bundled
`espeakng-loader` installed from `requirements.txt`.

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

The build script prefers `py -3.12`, then `py -3.11`, then `py -3.10`, and
rejects unsupported or broken `python` shims before creating the virtualenv.
It installs `requirements.txt`, then accepts either system `espeak-ng` on PATH
or bundled `espeakng-loader` from the venv before running PyInstaller.

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
├── main.py          Entry point — tray + server + UI
├── ui.py            Tkinter window (matches screenshot)
├── server.py        FastAPI REST API  (localhost:7778)
├── tts_engine.py    Kokoro wrapper + playback + save
├── engines/         Engine registry + OpenAI/ElevenLabs adapters
├── config.py        ~/.readout/config.json manager
├── history_store.py local recent-read history (off by default)
├── dependency_check.py first-run prerequisite diagnostics
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
| POST | /preview | `{engine?, voice?, speed?}` | Play short voice sample |
| POST | /stop | — | Stop playback |
| GET | /status | — | Health + current config |
| GET | /voices | — | Voice and engine catalogue |
| GET | /history | — | Local recent-read history if enabled |
| DELETE | /history | — | Clear local recent-read history |
| PATCH | /config | `{voice?, speed?, engine?, ...}` | Update settings |

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
  "elevenlabs_api_key": "",
  "allowed_origins":    [],
  "history_enabled":    false,
  "history_limit":      20
}
```

Edited live — no restart required.

Recent-read history is off by default. When enabled from `/control`, it stores
recent read text locally in `~/.readout/history.json` and can be cleared from
the control panel or `DELETE /history`.

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

## First-run dependency checks

At startup and in `GET /status`, ReadOut reports missing prerequisites with a
fix message:

- Python must be 3.10-3.12 for Kokoro compatibility.
- `kokoro` must be installed from `requirements.txt`.
- Kokoro must have an eSpeak NG runtime: either system `espeak-ng` on `PATH` or
  the bundled `espeakng-loader` package from `requirements.txt`.

These checks explain the issue before the first model warmup fails.

---

## Release gates

- Security assumptions live in `THREAT_MODEL.md`.
- Current app behavior is described in `FEATURE-SPEC.md`.
- Every release candidate should use `RELEASE_CHECKLIST.md`.
- Current roadmap readiness is summarized in `ROADMAP_STATUS.md`.
- Open owner decisions are gathered in `ARCHITECT_SIGNOFF.md`.
- Target packaging results should be recorded in `PACKAGING_VALIDATION.md`.
- Interactive desktop/browser smoke results should be recorded in
  `MANUAL_SMOKE_VALIDATION.md`.
- Upstream graph reconciliation notes live in `UPSTREAM_RECONCILIATION.md`.
- `.\tools\release_preflight.ps1` checks required release artifacts, upstream
  reconciliation, Python/espeak target evidence, secret scan, extension static
  smoke, Tk desktop static smoke, and optional test/live-server gates.
- `.\tools\upstream_reconciliation.ps1` prints the local `origin/main` graph
  and file delta without fetching, merging, or editing files.
- `.\tools\release_preflight.ps1 -RunSourceSmoke` also runs the in-process
  source HTTP smoke test without requiring a manually started app.
- `NEXT_EXECUTOR_PROMPT.md` is the current handoff prompt for finishing the
  remaining package validation gates without repeating already completed hosted
  packaging or manual smoke work.
- `MAC_RUNNER_HANDOFF.md` is the focused handoff for hosted or local macOS
  package-smoke refreshes.
- `.\tools\architect_signoff_check.ps1` verifies required Architect rows in
  `ARCHITECT_SIGNOFF.md` are accepted before release.
- `.\tools\packaging_validation_check.ps1` verifies target macOS/Windows
  packaging evidence in `PACKAGING_VALIDATION.md`.
- `.\tools\manual_smoke_check.ps1` verifies interactive Tk, `/control`, audio,
  and Chrome extension smoke evidence in `MANUAL_SMOKE_VALIDATION.md`.
- `.\tools\roadmap_audit.ps1` prints the current roadmap blocker summary without
  mutating the worktree.
- `.\tools\secret_scan.ps1` checks for common provider key literals before
  release.
- With ReadOut running, `.\tools\cors_origin_matrix.ps1` prints the live
  CORS/Origin proof matrix for the security gate.
- With ReadOut running, `.\tools\server_smoke.ps1` runs a non-audio API and
  `/control` smoke test. Add `-IncludeAudio` only when intentionally previewing
  a voice.
- With ReadOut running, `.\tools\control_workflow_smoke.ps1` performs a
  stateful non-audio `/control` backend workflow smoke: status refresh, config
  history toggle, history clear, and stop. It backs up and restores local
  `~/.readout/config.json` and `history.json`.
- `.\tools\control_browser_runtime_smoke.ps1` starts a temporary source server
  and validates the JavaScript-rendered `/control` status display in headless
  Chrome or Edge.
- `.\tools\control_browser_action_smoke.ps1` starts a temporary source server,
  opens `/control` in headless Chrome or Edge, clicks Preview, Speak, Save WAV,
  and Stop through the real page JavaScript, verifies the created WAV exists,
  removes the smoke WAV, and restores local config/history.
- `.\tools\extension_static_smoke.ps1` checks the Chrome extension manifest,
  least-privilege permissions, popup controls, endpoint wiring, context-menu
  IDs, and toast contract without launching Chrome.
- `.\tools\extension_runtime_smoke.ps1` starts a temporary source server, loads
  the unpacked extension through Chromium DevTools, verifies popup OFFLINE and
  READY text, allowlists the real extension origin, clicks popup Preview,
  invokes the service-worker context-menu selected-text handler, runs the shared
  Stop command path, and restores local config/history.
- `.\tools\tk_desktop_static_smoke.ps1` checks the Tk desktop source contract,
  including supported engine tabs, Preview Voice, Save WAV, stop/speak endpoint
  wiring, and config persistence without launching a GUI.
- `.\tools\tk_desktop_runtime_smoke.ps1` opens the real Tk desktop UI against a
  temporary source server, verifies engine/voice/speed persistence, exercises
  Preview, Speak, Save WAV, and Stop through the desktop UI methods, removes
  the smoke WAV, then restores local config/history.
- Before a Windows build, `.\tools\windows_packaging_prereqs.ps1` reports the
  supported Python, eSpeak NG runtime, and existing package-artifact state
  without installing dependencies or launching PyInstaller.
- The manual GitHub Actions workflow `.github/workflows/package-smoke.yml`
  builds Windows and macOS packages on hosted runners, runs package smoke
  helpers, and uploads package/evidence artifacts. The macOS job runs
  `./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui`
  and uploads `macos-tray-evidence` screenshots/probe logs when the runner can
  drive the menu-bar UI.
- For release status on this branch, recorded hosted package-smoke evidence
  satisfies Python 3.10-3.12 and `espeak-ng` prerequisite rows unless
  package/runtime source changes require fresh package artifacts.
- After a macOS build, `./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui`
  launches the packaged app, verifies the local server/control surface, tries
  to locate/click the menu-bar `Open Control Panel` item with System Events,
  runs preview, stop, speak, and stop, then quits the app.
- After a Windows build, `.\tools\windows_package_smoke.ps1 -ExePath
  dist\ReadOut\ReadOut.exe` launches the packaged exe, verifies the server, runs
  smoke checks, and stops the launched process. Add `-IncludeAudio` to verify
  packaged preview, speak, and stop endpoint lifecycle.

---

## Browser extension

See `extension/` directory (separate). The extension right-click menu posts
selected page text to `http://localhost:7778/speak`.

ReadOut only accepts browser requests from explicit local origins. After loading
the unpacked extension, copy its ID from `chrome://extensions` and add it to
`~/.readout/config.json`:

```json
{
  "allowed_origins": ["chrome-extension://YOUR_EXTENSION_ID"]
}
```

Local scripts and curl commands that send no `Origin` header still work.

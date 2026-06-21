# ReadOut — Feature Specification

**Status:** as-built description of the current codebase
**Date:** 2026-06-21
**Reported versions:** API server `1.0.0` (server.py) · extension `1.1` (manifest.json)
**Scope:** local-first desktop text-to-speech with a browser companion. This
document describes what the app *actually does today*, including partial /
cosmetic features and known gaps. It is a description of the current state, not
a roadmap.

---

## 1. Product summary

ReadOut turns selected or pasted text into spoken audio. Its headline mode runs
the **Kokoro 82M** model fully on-device (no API cost, no data leaves the
machine). It also offers two cloud engines (OpenAI TTS, ElevenLabs) as opt-in
alternatives. A local FastAPI server on `localhost:7778` is the hub; a Chrome
extension, a browser control panel, a Tkinter desktop window, and a system-tray
menu are all clients of that server.

**Core value props**
- Local-first / private by default (Kokoro never sends text off-device).
- "Read aloud" anything you select in the browser via right-click.
- Multiple engines and 18 local voices, switchable at runtime.
- Hot-reloadable config; no restart to change voice/speed/engine.

---

## 2. Architecture at a glance

```
                ┌──────────────────────── localhost:7778 (FastAPI) ─────────────────────┐
                │  /speak  /stop  /status  /voices  /config(PATCH)  /control  /(redirect) │
                └───────────────▲───────────────▲───────────────▲───────────────▲────────┘
                                │               │               │               │
            ┌───────────────────┘   ┌───────────┘     ┌─────────┘      ┌─────────┘
   Chrome extension (MV3)   Browser control panel   Tkinter desktop UI   System tray menu
   - context menus          (/control, served HTML) (ui.py; disabled on  (pystray; process
   - popup player/guide                              macOS 26+/Tk9)       anchor on macOS)
   - content toast

   Engine layer:  tts_engine.py (Kokoro local)  ·  server._speak_openai  ·  server._speak_elevenlabs
   Config:        ~/.readout/config.json (flat JSON, re-read every request)
   Audio out:     sounddevice (non-blocking play) + soundfile (WAV save)
```

**Process / thread model** (`main.py`): main thread = pystray tray (macOS
requires the tray on the main thread); daemon threads = uvicorn server, Kokoro
warm-up, and the Tk UI when enabled. Quitting the tray stops the process.

---

## 3. TTS engines

| Engine | ID | Location | Auth | Model / voices | Status |
|---|---|---|---|---|---|
| **Kokoro** | `kokoro` | On-device | none | Kokoro 82M, 18 voices, 24 kHz mono | Default, fully working |
| **OpenAI TTS** | `openai` | Cloud | `openai_api_key` | `tts-1`; alloy/echo/fable/onyx/nova/shimmer | Implemented (`_speak_openai`) |
| **ElevenLabs** | `elevenlabs` | Cloud | `elevenlabs_api_key` | `eleven_monolingual_v1`; Rachel default | Implemented (`_speak_elevenlabs`) |
| **Browser** | `browser` | (n/a) | none | Shown in desktop UI tabs only | **Cosmetic — not wired to the server** |

- `/speak` routes by the **config** `engine` value, not by a per-request engine
  field. Kokoro is the default path.
- Kokoro details: `KPipeline(lang_code=...)`, `lang_code` `a` = American EN /
  `b` = British EN. Output fixed at 24 kHz. On Apple Silicon,
  `PYTORCH_ENABLE_MPS_FALLBACK=1` is set for Metal acceleration.
- Cloud engines synthesize then play through `sounddevice`; errors return
  `{"status":"error","message":...}` rather than raising.

---

## 4. Voices & speed

- **18 Kokoro voices** with friendly labels (`tts_engine.VOICES`): American
  female `af_*` (heart, sky, bella, sarah, nicole, jessica, nova, river, kore,
  aoede), American male `am_*` (adam, echo, michael, fenrir), British `bf_emma`,
  `bf_isabella`, `bm_george`, `bm_lewis`. `af_heart` is the default.
- Exposed via `GET /voices` (labeled), the tray Voice submenu, the desktop UI
  dropdown, the extension popup, and the control panel.
- **Speed**: 0.5×–2.0× (default 1.0×) everywhere there's a slider.
- **Voice blending** (`af_heart:60,am_adam:40`): documented in README and the
  in-app guide. It is passed straight through to Kokoro — the app does not parse
  or validate it, so it works only insofar as the Kokoro pipeline accepts the
  blend syntax. *Not independently verified in this codebase.*

---

## 5. Local REST API (`localhost:7778`)

| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/` | — | 307 redirect → `/control` | |
| GET | `/control` | — | HTML | Self-contained browser control panel |
| POST | `/speak` | `{text, voice?, speed?, save?}` | `{status, voice, speed, saved_to?}` | Routes to active engine |
| POST | `/stop` | — | `{status:"stopped"}` | Stops `sounddevice` playback |
| GET | `/status` | — | `{status, engine, voice, speed, model_ready, load_error, version}` | Health + config snapshot |
| GET | `/voices` | — | `{voices:[{id,label}...]}` | 18 entries |
| PATCH | `/config` | `{voice?, speed?, engine?, always_save?, *_api_key?}` | `{status:"updated", config:{...}}` | Persists to disk |

- CORS is locked to `chrome-extension://` origins; arbitrary web pages are
  denied (see §11). A `TrustedHostMiddleware` also rejects non-loopback Host
  headers (DNS-rebinding guard), and interactive docs (`/docs`, `/openapi.json`)
  are disabled.
- `/speak` rejects text longer than `MAX_TEXT_CHARS` (20 000) before synthesis.
- `PATCH /config` never echoes secret values back — API keys are reduced to a
  boolean presence flag.
- `status` is `loading` while the model initializes, then `ready`.
- Verified live on 2026-06-21: server boots, reaches `ready`, serves `/control`
  (HTTP 200), `/voices` (18), and `/speak` produced a valid 5.15 s / 24 kHz WAV.

---

## 6. Browser control panel (`/control`)

A single self-contained HTML page embedded in `server.py`, served as the
**fallback UI** when the Tk desktop window can't run (the standard path on
current macOS). Features:

- Engine selector (Kokoro / OpenAI / ElevenLabs), voice dropdown (client-side
  voice lists per engine), text area, speed slider with live readout.
- Actions: **Speak**, **Speak + Save WAV**, **Stop**, **Refresh Status**.
- Status pill (Ready / Loading / Offline) driven by polling `GET /status`;
  engine/voice/speed changes persist via `PATCH /config`.
- Dark theme, acid-green (`#b8f542`) accent, responsive down to mobile widths.

---

## 7. Desktop UI (`ui.py`, Tkinter)

A richer native window styled to a dark "studio" mockup. **Auto-disabled on
macOS 26+ / Homebrew-Tk-9 builds** (detected via `otool -L` on `_tkinter`);
on those systems the app falls back to the browser control panel.

Implemented:
- Custom title bar (traffic-light dots, status dot), **Player / Guide** view
  tabs.
- Engine tabs (Kokoro · OpenAI · ElevenLabs · Browser) with LOCAL/API/FREE
  badges; model badge updates with selection.
- Text input with placeholder, **paste** / **clear** buttons, live character
  count (turns orange past 2000 chars).
- Voice dropdown (per-engine list) and speed slider (0.5–2.0×).
- Animated **waveform** canvas (idle vs. playing states).
- Play/Stop button (posts to `/speak` / `/stop` on a worker thread).
- **Save MP3** button (note: actually writes a **WAV**), with saving/saved
  feedback.
- **Recent / Queue** list (last 5 items with estimated duration).
- Built-in scrollable **Guide** (Quick Start, Extension, Voices, Engines,
  Saving, Config, API, Troubleshooting).
- Status dot polls `GET /status` every 3 s (green/orange/red).

Partial / cosmetic in the desktop UI (see §11): the **Browser** engine tab, the
**Auto-read** toggle, and the per-row queue **download (↓)** buttons have no
backing behavior; engine-tab selection does not `PATCH /config`, so it does not
actually switch the server's active backend.

---

## 8. System tray (`pystray`)

The tray icon is the **process anchor on macOS** and must not be removed. Menu:

- `ReadOut — Running` (disabled header)
- **Show Window** (or **Open Control Panel** when Tk is unavailable)
- **Open Control Panel** (when Tk is available)
- **Stop Audio**
- **Voice ▸** (all 18 voices)
- **Engine ▸** (Kokoro / OpenAI / ElevenLabs)
- **Quit**

Tray icon image loads `assets/icon.png`, or draws a soundwave fallback. Tray
notifications report the one-time model download (~300 MB) and "ready".

---

## 9. Chrome extension (MV3, `extension/`)

| Component | Feature |
|---|---|
| `background.js` (service worker) | Three context menus: **Read aloud** & **Read aloud & save WAV** (on text selection), **Stop reading** (anywhere). Posts selection to `localhost:7778/speak` / `/stop`. Injects the content script on demand (ping → `executeScript`). |
| `content.js` | Toast overlay on the page (acid-green success / red error), and a ping responder so the worker knows it's loaded. Silent no-op on `chrome://`/`edge://` pages. |
| `popup.html` + `popup.js` | **Player / Guide** tabs. Live status (READY / LOADING / OFFLINE) from `/status`. Engine selector (persists via `PATCH /config`), voice dropdown, speed slider. **Read Selection** grabs `window.getSelection()` from the active tab via `chrome.scripting`. **Stop** button. |
| `manifest.json` | MV3, v1.1. Permissions: `contextMenus`, `storage`, `activeTab`, `scripting`. Host permission: `http://localhost:7778/*`. |

The server URL is hardcoded to `localhost:7778` in `background.js` and
`popup.js` — changing the config port requires editing these too.

---

## 10. Configuration & runtime

**Config file** `~/.readout/config.json` (flat JSON, merged over `DEFAULTS`,
re-read on every request → hot-reload, no restart):

| Key | Default | Meaning |
|---|---|---|
| `voice` | `af_heart` | Active voice |
| `speed` | `1.0` | Playback rate |
| `lang_code` | `a` | `a`=American EN, `b`=British EN |
| `always_save` | `false` | Auto-save every utterance to WAV |
| `save_dir` | `~/Desktop/ReadOut` | WAV output folder |
| `port` | `7778` | Server port (7777 reserved for DaveLLM) |
| `engine` | `kokoro` | `kokoro` \| `openai` \| `elevenlabs` |
| `openai_api_key` | `""` | OpenAI auth |
| `elevenlabs_api_key` | `""` | ElevenLabs auth |
| `window_visible` | `true` | Open the desktop window on launch |

**Run modes & env toggles** (`main.py`):
- Default: tray + server + warm-up + (Tk UI or browser fallback).
- `--headless` (or `READOUT_HEADLESS=1`): API only, no tray/Tk; optionally opens
  the control panel. `--no-browser` suppresses that auto-open.
- `READOUT_FORCE_TK` / `READOUT_DISABLE_UI` force or disable the Tk window;
  `READOUT_AUTO_OPEN_CONTROL` controls control-panel auto-open.
- `main_app.py` is the packaged-macOS entry point: forces `READOUT_DISABLE_UI=1`
  and `READOUT_AUTO_OPEN_CONTROL=0` (tray + on-demand control panel).

**Audio & model lifecycle** (`tts_engine.py`): heavy imports (torch, kokoro,
sounddevice) are deferred to first use so the server starts fast. The Kokoro
pipeline is a thread-safe singleton; a `~/.readout/.model_ready` flag tracks
first-run. Playback is non-blocking via `sounddevice`; WAV files are written via
`soundfile` as `readout_<epoch>.wav` in `save_dir`.

**Packaging** (`ReadOut.spec`, `build_mac.sh`, `build_windows.ps1`): PyInstaller
builds `dist/ReadOut.app` (macOS menu-bar app, no Tk window) and
`dist/ReadOut/ReadOut.exe` (Windows). Asset paths resolve under PyInstaller's
`_MEIPASS` when bundled.

**Platform support:** Python 3.10–3.12 (Kokoro requires `<3.13`); macOS Apple
Silicon (MPS) and Windows; `espeak-ng` required as a system dependency.

---

## 11. Known gaps, inconsistencies & risks

**Hardened in the 2026-06-21 safety pass (now fixed):**

- **CORS locked down.** Replaced `allow_origins=["*"]` with a
  `chrome-extension://` origin regex; arbitrary web pages can no longer drive
  the local server. Added `TrustedHostMiddleware` (loopback-only Host) as a
  DNS-rebinding guard, and disabled `/docs` + `/openapi.json`.
- **API keys no longer echoed.** `PATCH /config` returns secrets as a boolean
  presence flag via `_safe_config()`, never the plaintext value.
- **`/speak` input cap.** Requests over `MAX_TEXT_CHARS` (20 000) are rejected
  before synthesis, preventing a runaway/DoS synthesis job.
- **Config file perms.** `~/.readout/config.json` is written `0600` (dir `0700`)
  so other local accounts can't read stored keys at rest.
- **Startup race fixed.** The Kokoro/transformers/torch import is now gated
  behind server readiness (`_wait_for_server`) and the server pins the stdlib
  asyncio loop, so the heavy import can no longer block uvicorn's bind on the
  Python import lock (a real startup hang).
- **Extension least privilege.** Dropped the unused `storage` permission
  (manifest `1.1` → `1.2`).

**Still open (behavioral, not addressed here):**

1. **Desktop UI "Browser" engine** is cosmetic — no server route exists.
2. **Desktop UI engine tabs don't switch the backend** — selecting OpenAI/
   ElevenLabs there doesn't `PATCH /config`, so `/speak` still uses the config
   engine. (The extension popup *does* persist engine changes.)
3. **Desktop UI Auto-read toggle** and **queue download (↓) buttons** have no
   behavior.
4. **"Save MP3" mislabeled** — the desktop button produces a WAV, not MP3.
5. **Tk desktop UI is effectively dormant** on current macOS; the browser
   control panel is the de-facto primary UI.
6. **Hardcoded port** in the extension (`background.js`, `popup.js`) must be
   kept in sync with `config.json` `port`.
7. **No automated tests** in the repo.

---

## 12. File map

| File | Role |
|---|---|
| `main.py` | Entry point; tray + server + warm-up + UI/fallback orchestration |
| `main_app.py` | Packaged-macOS entry (tray + control panel, no Tk) |
| `server.py` | FastAPI REST API + embedded `/control` panel + cloud-engine fallbacks |
| `tts_engine.py` | Kokoro pipeline, playback, WAV save, voice catalogue |
| `ui.py` | Tkinter desktop window (disabled on macOS 26+/Tk9) |
| `config.py` | `~/.readout/config.json` load/merge/save + asset paths |
| `extension/` | Chrome MV3 extension (background, content, popup) |
| `extension/design/tts-desktop-ui.html` | Static desktop-UI design mockup (reference) |
| `assets/` | Tray/app icons |
| `ReadOut.spec`, `build_mac.sh`, `build_windows.ps1` | PyInstaller packaging |

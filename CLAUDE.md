# ReadOut — Agent Instructions

## Project Overview

Local-first text-to-speech desktop app. Kokoro 82M model runs entirely on-device with zero API costs. FastAPI server on `localhost:7778` accepts calls from a companion Chrome extension. Supports Kokoro (local), OpenAI TTS, and ElevenLabs as engine options.

## Stack

- Python 3.10-3.12 (Kokoro requires < 3.13)
- FastAPI + uvicorn (local REST server on port 7778)
- Kokoro TTS engine (82M param model, ~300 MB, Hugging Face download)
- PyTorch with MPS Metal acceleration on Apple Silicon
- pystray (system tray icon)
- Tkinter (desktop UI window on non-macOS; `/control` is primary on macOS)
- Chrome extension (MV3, right-click to speak selected text)
- espeak-ng (phonemizer backend, required system dependency)

## Key Decisions

- Local-first: no data leaves the machine when using Kokoro engine.
- Port 7778 (DaveLLM uses 7777, both can run simultaneously).
- Config stored at `~/.readout/config.json`, hot-reloadable without restart.
- Kokoro model downloads on first run (~300 MB from Hugging Face).
- macOS: `/control` browser control panel is the primary UI. Tkinter can be forced with `READOUT_FORCE_TK=1` for troubleshooting, but packaged macOS flow stays tray + control panel.
- Recent-read history is local-only, off by default, and clearable from `/control` or `DELETE /history`.
- Thread layout: main thread = pystray tray, daemon threads = uvicorn server + Kokoro warmup + Tkinter UI on non-macOS when enabled.
- Tool execution and file paths use safe patterns (no shell=True).

## Documentation Maintenance

- **Issues**: Track in CLAUDE.md issue tracker table below
- **Session log**: Append to `/Users/daverobertson/Desktop/Code/95-docs-personal/today.csv` after each meaningful change

## Issue Tracker

| ID | Severity | Status | Title | Notes |
|----|----------|--------|-------|-------|
| 001 | P2 | resolved | Tk 9.0 crashes on macOS 26 | Python 3.11 (Tk 8.6) also crashes. Root cause: pystray NSApplication + Tk GetRGBA conflict. Fixed by skipping Tk UI on macOS 26+ |
| 002 | P1 | resolved | Control-panel commit reverted CORS + key redaction | Commit 93f3944 branched off a pre-security server.py and dropped the 0055aa7 hardening (wildcard CORS + unredacted PATCH /config). Restored, with regression tests in tests/test_server_cors.py and tests/test_server_api.py |
| 003 | P3 | mitigated | /speak and /config unauthenticated; /stop reachable cross-origin | Server now rejects untrusted browser `Origin` headers before endpoint side effects, so remote web pages cannot drive `/stop`, `/speak`, `/status`, `/voices`, or `/config`. Local no-Origin callers remain allowed for desktop UI, curl, and scripts. A shared-secret header is still the stronger future control if the extension protocol is revised. |

## Testing

Three layers, fastest first:

1. **Unit / integration** (`tests/test_*.py`) — in-process via Starlette
   `TestClient`. Mocks the heavy ML/audio stack (numpy, sounddevice, soundfile,
   kokoro) via fixtures in `tests/conftest.py`. Covers config
   load/merge/corruption, the Kokoro `speak()` flow, audio helpers, every REST
   endpoint, the CORS policy (regression guard for issue 002), API-key
   redaction, and the OpenAI/ElevenLabs fallbacks.
2. **Live end-to-end** (`tests/e2e/`) — boots the real ASGI app under uvicorn on
   an ephemeral port and drives it over a real socket (stdlib HTTP client).
   Proves routing/redirects, CORS behaviour over the wire, and that
   `PATCH /config` round-trips secrets to a real file while redacting the
   response. Audio/model leaf calls are stubbed, so it still needs no torch/kokoro.
3. **Manual / dev QA** (`docs/QA.md` + `scripts/qa_probe.py`) — for what CI
   can't do: real audio, the model download, live API keys, and the Chrome
   extension. `qa_probe.py` drives a *running* daemon (`python main.py`).

Commands:

- **Install dev deps**: `pip install -r requirements-dev.txt` (pytest, fastapi, httpx, uvicorn; no torch/kokoro)
- **Everything**: `python -m pytest`
- **Fast unit only**: `python -m pytest -m "not e2e"`
- **Live e2e only**: `python -m pytest tests/e2e`
- **Subprocess liveness smoke**: `scripts/smoke.sh`
- CI runs the full suite (layers 1 + 2) on push/PR across Python 3.10-3.12 (`.github/workflows/tests.yml`).

## Deployment

- **Run from source**: `source .venv/bin/activate && python main.py`
- **Build standalone**: `./build_mac.sh` produces `dist/ReadOut.app`
- **Prerequisites**: `brew install espeak-ng`, Python 3.10-3.12, `brew install python-tk@3.11`
- **Env var**: `PYTORCH_ENABLE_MPS_FALLBACK=1` (set in main.py for macOS)

## What Not To Do

- Do not require Python 3.13+ (Kokoro dependency constraint)
- Do not remove the local Kokoro engine option
- Do not send user text to external services without explicit engine selection
- Do not change the default port from 7778 (DaveLLM coordination)
- Do not remove the pystray tray icon (it is the process anchor on macOS)

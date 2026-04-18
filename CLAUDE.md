# ReadOut — Agent Instructions

## Project Overview

Local-first text-to-speech desktop app. Kokoro 82M model runs entirely on-device with zero API costs. FastAPI server on `localhost:7778` accepts calls from a companion Chrome extension. Supports Kokoro (local), OpenAI TTS, and ElevenLabs as engine options.

## Stack

- Python 3.10-3.12 (Kokoro requires < 3.13)
- FastAPI + uvicorn (local REST server on port 7778)
- Kokoro TTS engine (82M param model, ~300 MB, Hugging Face download)
- PyTorch with MPS Metal acceleration on Apple Silicon
- pystray (system tray icon)
- Tkinter (desktop UI window, disabled on macOS 26+ due to Tk/NSApplication crash)
- Chrome extension (MV3, right-click to speak selected text)
- espeak-ng (phonemizer backend, required system dependency)

## Key Decisions

- Local-first: no data leaves the machine when using Kokoro engine.
- Port 7778 (DaveLLM uses 7777, both can run simultaneously).
- Config stored at `~/.readout/config.json`, hot-reloadable without restart.
- Kokoro model downloads on first run (~300 MB from Hugging Face).
- macOS 26+: Tkinter UI disabled due to Tk/NSApplication `macOSVersion` selector crash. Tray + server + Chrome extension remain fully functional.
- Thread layout: main thread = pystray tray, daemon threads = uvicorn server + Kokoro warmup + Tkinter UI (when available).
- Tool execution and file paths use safe patterns (no shell=True).

## Documentation Maintenance

- **Issues**: Track in CLAUDE.md issue tracker table below
- **Session log**: Append to `/Users/daverobertson/Desktop/Code/95-docs-personal/today.csv` after each meaningful change

## Issue Tracker

| ID | Severity | Status | Title | Notes |
|----|----------|--------|-------|-------|
| 001 | P2 | resolved | Tk 9.0 crashes on macOS 26 | Python 3.11 (Tk 8.6) also crashes. Root cause: pystray NSApplication + Tk GetRGBA conflict. Fixed by skipping Tk UI on macOS 26+ |

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

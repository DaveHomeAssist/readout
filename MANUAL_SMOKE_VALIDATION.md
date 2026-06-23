# ReadOut Manual Smoke Validation

Last updated: 2026-06-23 06:36 -04:00

Use this worksheet for release checks that require an interactive desktop,
browser, extension, or audible playback path. Fill it on the intended release
machine, then run `.\tools\manual_smoke_check.ps1`.

Release-ready rows should use `PASS`, `PASSED`, `OK`, `DONE`, or `COMPLETE`
and include evidence/notes. Use `ACCEPTED GAP` only when the evidence/notes
column names the accepted risk.

## Source Control Panel Smoke

| Check | Result | Evidence |
|---|---|---|
| `/control` opens on `127.0.0.1:7778` | TBD | |
| `/control` status display updates | TBD | |
| `/control` Preview Voice plays audio | TBD | |
| `/control` Speak text works | TBD | |
| `/control` Speak + Save WAV creates WAV | TBD | |
| `/control` Stop playback works | TBD | |
| `/control` history toggle and Clear History work | TBD | |

## Tk Desktop Smoke

| Check | Result | Evidence |
|---|---|---|
| Tk desktop opens on supported non-macOS target or `READOUT_FORCE_TK=1` | TBD | |
| Desktop engine, voice, and speed controls persist through backend config | TBD | |
| Desktop Preview Voice plays audio | TBD | |
| Desktop Speak, Save WAV, and Stop work | TBD | |

## Chrome Extension Smoke

| Check | Result | Evidence |
|---|---|---|
| Extension origin added to `allowed_origins` | TBD | |
| Popup shows READY when server is up | TBD | |
| Popup shows OFFLINE or next action when server is down | TBD | |
| Popup Preview Voice works | TBD | |
| Context menu Read aloud works on selected page text | TBD | |
| Extension Stop playback works | TBD | |

## Manual Smoke Summary

| Item | Status | Notes |
|---|---|---|
| Source `/control` manual smoke | Pending | |
| Tk desktop manual smoke | Pending | |
| Chrome extension manual smoke | Pending | |

# ReadOut Manual Smoke Validation

Last updated: 2026-06-23 19:53 -04:00

Use this worksheet for release checks that require an interactive desktop,
browser, extension, or audible playback path. Fill it on the intended release
machine, then run `.\tools\manual_smoke_check.ps1`.

Release-ready rows should use `PASS`, `PASSED`, `OK`, `DONE`, or `COMPLETE`
and include evidence/notes. Use `ACCEPTED GAP` only when the evidence/notes
column names the accepted risk.

Automated non-audio support evidence can reduce the manual scope, but it does
not replace rows that require human audio, browser extension, or desktop visual
confirmation.

## Automated Non-Audio Support Evidence

| Check | Result | Evidence |
|---|---|---|
| Source `/control` backend workflow | PASS | 2026-06-23 19:30 -04:00: temporary source server on `127.0.0.1:7778`; `.\tools\server_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed `/status`, `/voices`, `/history`, and `/control`; `.\tools\control_workflow_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed loopback target, status refresh backend, control panel page, history config toggle, history refresh, Clear History backend, Stop backend, and byte-preserving local config/history restore. |
| Chrome extension static contract | PASS | 2026-06-23 17:58 -04:00: `.\tools\extension_static_smoke.ps1` passed Manifest V3, permissions, exact localhost host permission, service worker, default popup, icons, popup controls, popup endpoint wiring, context-menu IDs, `/speak` and `/stop` background wiring, and content toast contract. This does not replace Chrome runtime popup/audio/manual smoke rows. |
| Tk desktop static contract | PASS | 2026-06-23 18:21 -04:00: `.\tools\tk_desktop_static_smoke.ps1` passed Tk app class, localhost server target, supported engine tabs, no Browser engine tab, Preview Voice, Save WAV, play/stop controls, config persistence wiring, `/voices`, `/status`, `/preview`, `/speak`, and `/stop` endpoint wiring. This does not replace desktop launch/audio/manual smoke rows. |
| Tk desktop runtime non-audio workflow | PASS | 2026-06-23 19:40 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1` opened the Tk window on a 1920x1080 Windows desktop, found engine/voice/preview/save/play controls, persisted engine `openai`, voice `nova`, and speed `1.7` through the backend, stopped the temporary source server, and restored local config/history. This does not replace desktop audible playback rows. |
| Source `/control` browser status runtime | PASS | 2026-06-23 19:53 -04:00: `.\tools\control_browser_runtime_smoke.ps1` started a temporary source server on `127.0.0.1:7778`, opened `/control` in headless Chrome, and verified the rendered DOM updated from the initial waiting/offline state to backend status `ready` with label `Ready` and dependency feedback visible. This does not replace audible source control rows. |

## Source Control Panel Smoke

| Check | Result | Evidence |
|---|---|---|
| `/control` opens on `127.0.0.1:7778` | PASS | 2026-06-23 19:30 -04:00: live source server at `http://127.0.0.1:7778`; `server_smoke.ps1` reported `GET /control PASS` with required controls present; server stdout recorded `GET /control HTTP/1.1 200 OK`. |
| `/control` status display updates | PASS | 2026-06-23 19:53 -04:00: `.\tools\control_browser_runtime_smoke.ps1` reported `/control status display updates PASS` with DOM `state=ready`, `label=Ready`, and feedback updated from `/status`; server detail was `status=ready; engine=kokoro; dependency_issues=3`. |
| `/control` Preview Voice plays audio | TBD | |
| `/control` Speak text works | TBD | |
| `/control` Speak + Save WAV creates WAV | TBD | |
| `/control` Stop playback works | TBD | |
| `/control` history toggle and Clear History work | PASS | 2026-06-23 19:30 -04:00: non-audio source backend evidence; `control_workflow_smoke.ps1` passed `History toggle via config`, `History status refresh`, `Clear History backend`, and `Restore local config/history`. |

## Tk Desktop Smoke

| Check | Result | Evidence |
|---|---|---|
| Tk desktop opens on supported non-macOS target or `READOUT_FORCE_TK=1` | PASS | 2026-06-23 19:40 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1` reported `Tk window opens PASS` with ReadOut title, size `560x680`, screen `1920x1080`, plus `Tk controls present PASS`. |
| Desktop engine, voice, and speed controls persist through backend config | PASS | 2026-06-23 19:40 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1` reported `Desktop engine persists PASS`, `Desktop voice persists PASS`, and `Desktop speed persists PASS`; backend `/status` reflected engine `openai`, voice `nova`, speed `1.7`; local config/history restored. |
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

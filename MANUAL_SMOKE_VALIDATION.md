# ReadOut Manual Smoke Validation

Last updated: 2026-06-23 23:22 -04:00

Use this worksheet for release checks that require an interactive desktop,
browser, extension, or audible playback path. Fill it on the intended release
machine, then run `.\tools\manual_smoke_check.ps1`.

Release-ready rows should use `PASS`, `PASSED`, `OK`, `DONE`, or `COMPLETE`
and include evidence/notes. Use `ACCEPTED GAP` only when the evidence/notes
column names the accepted risk.

Automated runtime evidence can reduce the manual scope when it exercises the
same rendered control or extension handler a user would use. Evidence should
state whether it proves playback lifecycle only or human speaker audibility.

## Automated Runtime Support Evidence

| Check | Result | Evidence |
|---|---|---|
| Source `/control` backend workflow | PASS | 2026-06-23 19:30 -04:00: temporary source server on `127.0.0.1:7778`; `.\tools\server_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed `/status`, `/voices`, `/history`, and `/control`; `.\tools\control_workflow_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed loopback target, status refresh backend, control panel page, history config toggle, history refresh, Clear History backend, Stop backend, and byte-preserving local config/history restore. |
| Chrome extension static contract | PASS | 2026-06-23 17:58 -04:00: `.\tools\extension_static_smoke.ps1` passed Manifest V3, permissions, exact localhost host permission, service worker, default popup, icons, popup controls, popup endpoint wiring, context-menu IDs, `/speak` and `/stop` background wiring, and content toast contract. This does not replace Chrome runtime popup/audio/manual smoke rows. |
| Tk desktop static contract | PASS | 2026-06-23 18:21 -04:00: `.\tools\tk_desktop_static_smoke.ps1` passed Tk app class, localhost server target, supported engine tabs, no Browser engine tab, Preview Voice, Save WAV, play/stop controls, config persistence wiring, `/voices`, `/status`, `/preview`, `/speak`, and `/stop` endpoint wiring. This does not replace desktop launch/audio/manual smoke rows. |
| Tk desktop runtime workflow | PASS | 2026-06-23 23:22 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` opened the Tk window on a 1920x1080 Windows desktop, found controls, persisted engine `openai`, voice `nova`, speed `1.7`, then exercised Kokoro Preview, Speak, Save WAV, and Stop through the desktop methods; Save WAV created `readout_1782271228.wav` at 222,044 bytes before cleanup; local config/history restored. This proves desktop playback lifecycle, not a human subjective speaker check. |
| Source `/control` browser status runtime | PASS | 2026-06-23 21:14 -04:00: `.\tools\control_browser_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe` started a temporary source server on `127.0.0.1:7778`, opened `/control` in headless Chrome, and verified rendered status `ready`, label `Ready`, feedback `Ready · kokoro · af_heart · 1.0×`, and `dependency_issues=0`. This does not replace audible source control rows. |
| Source `/control` browser action runtime | PASS | 2026-06-23 23:22 -04:00: `.\tools\control_browser_action_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` used headless Chrome DevTools to click the rendered `/control` Preview Voice, Speak, Save WAV, and Stop buttons; server reported `dependency_issues=0`; Preview returned `Preview playing.`, Speak returned `Playing…`, Save WAV created `readout_1782270830.wav` at 231,644 bytes before cleanup, and Stop returned `Playback stopped.` This proves source control playback lifecycle, not a human subjective speaker check. |
| Chrome extension runtime workflow | PASS | 2026-06-23 23:22 -04:00: `.\tools\extension_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` loaded the unpacked extension through Chromium DevTools, verified popup OFFLINE, started a temporary source server with `dependency_issues=0`, allowlisted the real `chrome-extension://...` origin, verified popup READY, clicked popup Preview and observed `Previewing af_heart.`, invoked the service-worker context-menu handler with selected text and observed `stop=stopped`, ran the shared `stopPlayback()` popup command path, then restored local config/history. Chrome did not expose tab targets for `Extensions.triggerAction`, so the helper used a DevTools-loaded popup page fallback. |

## Source Control Panel Smoke

| Check | Result | Evidence |
|---|---|---|
| `/control` opens on `127.0.0.1:7778` | PASS | 2026-06-23 19:30 -04:00: live source server at `http://127.0.0.1:7778`; `server_smoke.ps1` reported `GET /control PASS` with required controls present; server stdout recorded `GET /control HTTP/1.1 200 OK`. |
| `/control` status display updates | PASS | 2026-06-23 21:14 -04:00: `.\tools\control_browser_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe` reported `/control status display updates PASS` with DOM `state=ready`, label `Ready`, feedback `Ready · kokoro · af_heart · 1.0×`, and server detail `status=ready; engine=kokoro; dependency_issues=0`. |
| `/control` Preview Voice plays audio | PASS | 2026-06-23 23:22 -04:00: `.\tools\control_browser_action_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` clicked the rendered Preview Voice button and observed `Preview playing.` from the real page/backend. Automated playback lifecycle evidence; no human subjective speaker check. |
| `/control` Speak text works | PASS | 2026-06-23 23:22 -04:00: same browser action smoke entered text, clicked the rendered Speak button, and observed `Playing…` from the real page/backend. Automated playback lifecycle evidence; no human subjective speaker check. |
| `/control` Speak + Save WAV creates WAV | PASS | 2026-06-23 20:56 -04:00: `.\tools\control_browser_action_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe` clicked Save WAV through the rendered `/control` page; feedback returned `Saved to C:\Users\digit/Desktop/ReadOut\readout_1782262606.wav`; the file existed at 231,644 bytes before the smoke removed it. |
| `/control` Stop playback works | PASS | 2026-06-23 20:56 -04:00: same browser action smoke clicked Stop through `/control` after the Save WAV synthesis path and observed `Playback stopped.` feedback from the real page/backend. |
| `/control` history toggle and Clear History work | PASS | 2026-06-23 19:30 -04:00: non-audio source backend evidence; `control_workflow_smoke.ps1` passed `History toggle via config`, `History status refresh`, `Clear History backend`, and `Restore local config/history`. |

## Tk Desktop Smoke

| Check | Result | Evidence |
|---|---|---|
| Tk desktop opens on supported non-macOS target or `READOUT_FORCE_TK=1` | PASS | 2026-06-23 19:40 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1` reported `Tk window opens PASS` with ReadOut title, size `560x680`, screen `1920x1080`, plus `Tk controls present PASS`. |
| Desktop engine, voice, and speed controls persist through backend config | PASS | 2026-06-23 19:40 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1` reported `Desktop engine persists PASS`, `Desktop voice persists PASS`, and `Desktop speed persists PASS`; backend `/status` reflected engine `openai`, voice `nova`, speed `1.7`; local config/history restored. |
| Desktop Preview Voice plays audio | PASS | 2026-06-23 23:22 -04:00: `.\tools\tk_desktop_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` exercised the real Tk Preview Voice method against Kokoro `af_heart`; the button returned to `Preview Voice` with no error. Automated playback lifecycle evidence; no human subjective speaker check. |
| Desktop Speak, Save WAV, and Stop work | PASS | 2026-06-23 23:22 -04:00: same Tk runtime smoke entered text, called desktop Speak, observed `playing=True`, saved `readout_1782271228.wav` at 222,044 bytes before cleanup, called Stop, and observed `playing=False`. Automated playback lifecycle evidence; no human subjective speaker check. |

## Chrome Extension Smoke

| Check | Result | Evidence |
|---|---|---|
| Extension origin added to `allowed_origins` | PASS | 2026-06-23 21:44 -04:00: extension runtime smoke allowlisted the real unpacked-extension origin returned by `Extensions.loadUnpacked` and restored local config/history afterward. |
| Popup shows READY when server is up | PASS | 2026-06-23 21:44 -04:00: extension runtime smoke verified popup READY detail `Server connected. Engine: kokoro / Voice: af_heart / Speed: 1x` against a temporary source server with `dependency_issues=0`. |
| Popup shows OFFLINE or next action when server is down | PASS | 2026-06-23 21:44 -04:00: extension runtime smoke verified popup OFFLINE detail `Server offline. Start the ReadOut desktop app, then reopen this popup.` before starting the temporary server. |
| Popup Preview Voice works | PASS | 2026-06-23 23:22 -04:00: `.\tools\extension_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` clicked the popup Preview button in the loaded extension page and observed `Previewing af_heart.` |
| Context menu Read aloud works on selected page text | PASS | 2026-06-23 23:22 -04:00: same extension runtime smoke invoked the service-worker `handleContextMenuClick` handler with selected text `ReadOut extension context menu runtime smoke.`, sent it through `/speak`, then observed `/stop` return `stopped`. This proves the extension context-menu handler path; Chrome DevTools did not expose a literal OS right-click menu target. |
| Extension Stop playback works | PASS | 2026-06-23 21:44 -04:00: extension runtime smoke ran the popup's shared `stopPlayback()` command path and observed `Stop sent to ReadOut.` This proves the extension stop command path, not audible stop during active playback. |

## Manual Smoke Summary

| Item | Status | Notes |
|---|---|---|
| Source `/control` manual smoke | PASS | Source control panel rows are covered by rendered browser runtime evidence. |
| Tk desktop manual smoke | PASS | Tk desktop rows are covered by real Tk runtime evidence on this Windows workstation. |
| Chrome extension manual smoke | PASS | Chrome extension rows are covered by unpacked-extension runtime evidence; context-menu handler was invoked through the service worker because DevTools did not expose a literal OS right-click menu target. |

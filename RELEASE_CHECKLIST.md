# ReadOut Release Checklist

Use this checklist for every release candidate.

## 1. Preconditions
- [ ] Confirm the release branch is up to date with `origin/main`, or document and accept any reviewed remote delta in `UPSTREAM_RECONCILIATION.md`.
- [ ] Run roadmap audit: `.\tools\roadmap_audit.ps1`.
- [ ] Read the current handoff packet: `NEXT_EXECUTOR_PROMPT.md`.
- [ ] Run upstream reconciliation report: `.\tools\upstream_reconciliation.ps1`.
- [ ] Run Architect sign-off check: `.\tools\architect_signoff_check.ps1`.
- [ ] Run packaging validation check after target smoke evidence is filled: `.\tools\packaging_validation_check.ps1`.
- [ ] Run manual smoke validation check after interactive evidence is filled: `.\tools\manual_smoke_check.ps1`.
- [ ] Run local release preflight: `.\tools\release_preflight.ps1` (includes upstream reconciliation, secret scan, extension static smoke, and Tk desktop static smoke).
- [ ] If target hardware is unavailable locally, run the manual GitHub Actions package-smoke workflow and attach its uploaded evidence artifacts.
- [ ] Use Python 3.10-3.12.
- [ ] Confirm `espeak-ng --version` works on the target machine.
- [ ] Confirm `python -m pip install -r requirements.txt` completes in the release environment.
- [ ] Run secret scan: `.\tools\secret_scan.ps1`.
- [ ] Run source-server preflight smoke: `.\tools\release_preflight.ps1 -RunSourceSmoke`.
- [ ] Run Chrome extension static smoke: `.\tools\extension_static_smoke.ps1`.
- [ ] Run Tk desktop static smoke: `.\tools\tk_desktop_static_smoke.ps1`.
- [ ] Confirm no provider API keys or private values are committed or pasted into logs.

## 2. Security Gate
- [ ] Review `THREAT_MODEL.md` and confirm local-only assumptions still hold.
- [ ] Run CORS/origin regression tests: `python -m pytest tests/test_server_cors.py`.
- [ ] With ReadOut running, run live CORS proof matrix: `.\tools\cors_origin_matrix.ps1`.
- [ ] Confirm unknown origins receive `403` and no `Access-Control-Allow-Origin`.
- [ ] Confirm `/config` responses redact `openai_api_key` and `elevenlabs_api_key`.
- [ ] Confirm recent-read history is off by default and clearable.

## 3. Test Gate
- [ ] Run full test suite: `python -m pytest`.
- [ ] Run source live HTTP smoke: `python -m pytest tests/test_live_http_smoke.py` or `.\tools\release_preflight.ps1 -RunSourceSmoke`.
- [ ] Record pass/fail output in `MILESTONE_LOG.md`.
- [ ] With ReadOut running, run non-audio API/control smoke: `.\tools\server_smoke.ps1`.
- [ ] With ReadOut running, run non-audio control workflow smoke: `.\tools\control_workflow_smoke.ps1`.
- [ ] Run a manual `/control` smoke test:
  - [ ] Open `http://127.0.0.1:7778/control`.
  - [ ] Check status display.
  - [ ] Preview a voice.
  - [ ] Speak text.
  - [ ] Save WAV.
  - [ ] Stop playback.
  - [ ] Toggle history on/off and clear history.
  - [ ] Record results in `MANUAL_SMOKE_VALIDATION.md`.
- [ ] Run a Chrome extension smoke test:
  - [ ] Confirm extension origin is allowlisted.
  - [ ] Check popup READY/LOADING/OFFLINE/error text.
  - [ ] Preview a voice.
  - [ ] Read selected text.
  - [ ] Stop playback.
  - [ ] Record results in `MANUAL_SMOKE_VALIDATION.md`.

## 4. macOS Build Gate
- [ ] Run `./build_mac.sh` on macOS with Python 3.10-3.12.
- [ ] Confirm the script reports `Python:` and `espeak-ng: OK` before dependency install.
- [ ] Confirm `dist/ReadOut.app` exists.
- [ ] Run packaged lifecycle smoke: `chmod +x tools/mac_package_smoke.sh && ./tools/mac_package_smoke.sh --app dist/ReadOut.app`.
- [ ] Confirm tray icon appears.
- [ ] Confirm tray `Open Control Panel` opens `/control`.
- [ ] Confirm lifecycle: start, preview, speak, stop, quit.
- [ ] Fill P3-A1 section in `PACKAGING_VALIDATION.md`.
- [ ] If using CI evidence, attach the `readout-macos-package-smoke` artifact and note any remaining manual tray-icon gap.
- [ ] Record build path, app size, and smoke results in `MILESTONE_LOG.md`.

## 5. Windows Build Gate
- [ ] Run prerequisite report: `.\tools\windows_packaging_prereqs.ps1`.
- [ ] Run `.\build_windows.ps1` on Windows with Python 3.10-3.12.
- [ ] Confirm the script reports the selected Python source and `espeak-ng: OK` before dependency install.
- [ ] Confirm `dist\ReadOut\ReadOut.exe` exists.
- [ ] Run packaged lifecycle smoke: `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe`.
- [ ] Confirm `/control` workflows work.
- [ ] Confirm lifecycle: start, preview, speak, stop, quit.
- [ ] Fill P3-A2 section in `PACKAGING_VALIDATION.md`.
- [ ] If using CI evidence, attach the `readout-windows-package-smoke` artifact.
- [ ] Record build path and smoke results in `MILESTONE_LOG.md`.

## 6. Release Notes
- [ ] Summarize user-visible changes.
- [ ] List known risks and rollback steps.
- [ ] Include exact test/build commands and outcomes.
- [ ] Complete `ARCHITECT_SIGNOFF.md` and copy final decisions into `DECISION_LOG.md`.

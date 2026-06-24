# ReadOut Packaging Validation Worksheet

Last updated: 2026-06-24 00:30 -04:00

Use this worksheet on the target packaging machines. Paste completed tables into
`MILESTONE_LOG.md` under the matching P3-A1 or P3-A2 entry.
When local target hardware is unavailable, the manual GitHub Actions workflow
`.github/workflows/package-smoke.yml` can produce hosted-runner package and
smoke evidence artifacts, including macOS menu-bar screenshots/probe logs when
`--include-tray-ui` succeeds.

After filling target results, run `.\tools\packaging_validation_check.ps1`.
Release-ready rows should use `PASS`, `PASSED`, `OK`, `DONE`, or `COMPLETE`
and include evidence/notes. Use `ACCEPTED GAP` only when the evidence/notes
column names the accepted risk.

## Preconditions

| Check | Result | Notes |
|---|---|---|
| `ARCHITECT_SIGNOFF.md` reviewed | PASS | Architect decisions are accepted in the Notion Architect sign-off page and transcribed in `ARCHITECT_SIGNOFF.md`; `tools/architect_signoff_check.ps1` is expected to pass. |
| `.\tools\release_preflight.ps1` or target equivalent run | PASS | Target-equivalent GitHub Actions package-smoke run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385) passed on commit `10d7550`; macOS package smoke included `--include-audio --include-tray-ui` and proved preview/stop/speak/stop audio lifecycle plus tray menu evidence. |
| GitHub Actions `package-smoke` workflow run, if used | PASS | Run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385) passed; macOS job `83117008362` and Windows job `83117008329` both succeeded. |
| Python 3.10-3.12 confirmed | PASS | Tests workflow [28062313482](https://github.com/DaveHomeAssist/readout/actions/runs/28062313482) passed Python 3.10, 3.11, and 3.12 jobs on the package-producing commit; package-smoke used Python 3.12 on Windows and macOS. |
| `espeak-ng` confirmed on PATH | PASS | Package-smoke run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500) passed `Install espeak-ng` and package build steps on both Windows and macOS. Current local Windows build also passed with bundled `espeakng_loader` instead of system `espeak-ng` on PATH. |
| Full test suite run | PASS | Tests workflow [28062313482](https://github.com/DaveHomeAssist/readout/actions/runs/28062313482) passed on head `440cb577875dfd2aad8a359df972471e5c207511` for Python 3.10, 3.11, and 3.12. |

## P3-A1 - macOS App Validation

Run on macOS:

```bash
./build_mac.sh
chmod +x tools/mac_package_smoke.sh
./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui
```

Non-audio fallback smoke, only when the target cannot produce audio output and
the gap is explicitly accepted:

```bash
./tools/mac_package_smoke.sh --app dist/ReadOut.app
```

The `--include-tray-ui` mode attempts a macOS menu-bar UI smoke with System
Events, captures `macos-package-evidence` screenshots, clicks the tray `Open
Control Panel` item, and verifies the packaged app recorded a `/control` open
through `READOUT_CONTROL_OPEN_PROBE`.

Record:

| Check | Result | Evidence |
|---|---|---|
| `./build_mac.sh` completed | PASS | GitHub Actions run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385), macOS job `83117008362`: Python 3.12.10, `espeak-ng: OK`, `Build complete: dist/ReadOut.app`, size `575M`. |
| `dist/ReadOut.app` exists | PASS | macOS package smoke reported `App bundle exists PASS`; artifact `readout-macos-package-smoke` id `7840118532`, digest `sha256:5868986c68411cd2ee7370a36835ecbcf2017c5335a72de9e9bf79124bcfd369`. |
| `tools/mac_package_smoke.sh` passed | PASS | macOS package smoke passed app launch, server ready, `/status`, `/voices`, `/history`, `/control`, preview/stop/speak/stop audio lifecycle, menu-bar/tray UI smoke, blocked-origin, and clean-quit checks in run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385). |
| Menu-bar/tray icon visible | PASS | macOS package smoke reported `Menu-bar/tray icon visible PASS`; System Events located the ReadOut status menu and saved `macos-tray-evidence` screenshots in artifact `7840118532`. |
| Tray `Open Control Panel` opens `/control` | PASS | macOS package smoke reported `Tray Open Control Panel opens /control PASS`; the tray click launched a browser process with callback target `http://127.0.0.1:7778/control`, recorded in `macos-tray-evidence`. |
| macOS preview/speak/stop lifecycle verified | PASS | GitHub Actions run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385) ran `./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui --evidence-dir macos-tray-evidence` and reported `POST /preview PASS status=playing; preview=true`, `POST /stop after preview PASS status=stopped`, `POST /speak PASS status=playing`, and `POST /stop after speak PASS status=stopped`. |
| App quits cleanly | PASS | macOS package smoke reported `App quits cleanly PASS` with no app process or server response after quit in run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385). |

## P3-A2 - Windows App Validation

Run on Windows:

```powershell
.\build_windows.ps1
.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe
```

Optional audio preview smoke:

```powershell
.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -IncludeAudio
```

Record:

| Check | Result | Evidence |
|---|---|---|
| `.\build_windows.ps1` completed | PASS | 2026-06-23 22:55 -04:00 local Windows build used Python 3.12.10 from `.venv`, installed pinned `requirements.txt` including `torch>=2.10,<2.12` and `en_core_web_sm`, forced core VC runtime DLLs from `System32`, bundled Kokoro/spaCy model files, reported `espeak-ng: OK (bundled espeakng_loader)`, ran PyInstaller, and printed `Build complete: dist\ReadOut\ReadOut.exe`. |
| `dist\ReadOut\ReadOut.exe` exists | PASS | 2026-06-23 22:56 -04:00 local `Test-Path` confirmed `dist\ReadOut\ReadOut.exe`; file size was 66,119,978 bytes. |
| `tools\windows_package_smoke.ps1` passed | PASS | 2026-06-23 22:59 -04:00 local `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 240 -IncludeAudio` passed executable launch, server ready, preview/speak/stop audio endpoint smoke, CORS origin matrix, and process stop. |
| Server starts on `127.0.0.1:7778` | PASS | Local Windows package smoke reported `Server ready PASS` with `status=loading; engine=kokoro; dependency_issues=0`; later debug status after runtime fixes reported `load_error=null` and `dependency_issues=[]`. |
| `/control` opens and displays controls | PASS | Local Windows package smoke helper reported `GET /control PASS` with required controls present. |
| Windows preview/speak/stop lifecycle verified | PASS | Local Windows package smoke with `-IncludeAudio` reported `POST /preview PASS status=playing`, `POST /stop after preview PASS status=stopped`, `POST /speak PASS status=playing`, and `POST /stop after speak PASS status=stopped`. |
| App process stops cleanly | PASS | Windows package smoke reported `Stop packaged exe PASS` for pid `57828`. |

## Release Evidence Summary

| Item | Status | Notes |
|---|---|---|
| P3-A1 macOS packaging | PASS | Hosted macOS package-smoke run [28074903385](https://github.com/DaveHomeAssist/readout/actions/runs/28074903385) passed build, `/control`, preview/stop/speak/stop audio lifecycle, visible menu-bar/tray evidence, tray `Open Control Panel` to `/control`, blocked-origin, and clean quit; artifact `7840118532` records digest `sha256:5868986c68411cd2ee7370a36835ecbcf2017c5335a72de9e9bf79124bcfd369`. |
| P3-A2 Windows packaging | PASS | Current local Windows build and package smoke with `-IncludeAudio` passed `/control`, CORS, preview, speak, stop, and clean process stop with bundled `espeakng_loader`, bundled spaCy model files, and System32 VC runtime DLLs. |
| P3-A4 release checklist accepted | PASS | Architect accepted `RELEASE_CHECKLIST.md` as the reusable release gate; package/manual evidence rows still control final release readiness. |

## Known Acceptable Gaps

List any gap the Architect explicitly accepts for a release candidate.

| Gap | Accepted By | Date | Mitigation |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

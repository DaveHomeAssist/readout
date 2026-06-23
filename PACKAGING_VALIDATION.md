# ReadOut Packaging Validation Worksheet

Last updated: 2026-06-23 18:37 -04:00

Use this worksheet on the target packaging machines. Paste completed tables into
`MILESTONE_LOG.md` under the matching P3-A1 or P3-A2 entry.
When local target hardware is unavailable, the manual GitHub Actions workflow
`.github/workflows/package-smoke.yml` can produce hosted-runner package and
non-audio smoke evidence artifacts. CI evidence still does not replace manual
tray/menu-bar visual confirmation or audible preview checks unless the
Architect explicitly accepts that gap.

After filling target results, run `.\tools\packaging_validation_check.ps1`.
Release-ready rows should use `PASS`, `PASSED`, `OK`, `DONE`, or `COMPLETE`
and include evidence/notes. Use `ACCEPTED GAP` only when the evidence/notes
column names the accepted risk.

## Preconditions

| Check | Result | Notes |
|---|---|---|
| `ARCHITECT_SIGNOFF.md` reviewed | Pending | Required rows are still unsigned. |
| `.\tools\release_preflight.ps1` or target equivalent run | PASS | Target-equivalent GitHub Actions package-smoke run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132) passed on current head `06369b46b3d929adcec1cba1c1ebc706a548b0c9`; local full preflight remains blocked by sign-off and manual evidence gates. |
| GitHub Actions `package-smoke` workflow run, if used | PASS | Run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132) passed; Windows job `83075924486` and macOS job `83075924465` both succeeded. |
| Python 3.10-3.12 confirmed | PASS | Tests workflow [28061248462](https://github.com/DaveHomeAssist/readout/actions/runs/28061248462) passed Python 3.10, 3.11, and 3.12 jobs on current head; package-smoke used Python 3.12 on Windows and macOS. |
| `espeak-ng` confirmed on PATH | PASS | Package-smoke run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132) passed `Install espeak-ng` and package build steps on both Windows and macOS. |
| Full test suite run | PASS | Tests workflow [28061248462](https://github.com/DaveHomeAssist/readout/actions/runs/28061248462) passed on head `06369b46b3d929adcec1cba1c1ebc706a548b0c9` for Python 3.10, 3.11, and 3.12. |

## P3-A1 - macOS App Validation

Run on macOS:

```bash
./build_mac.sh
chmod +x tools/mac_package_smoke.sh
./tools/mac_package_smoke.sh --app dist/ReadOut.app
```

Optional audio preview smoke:

```bash
./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio
```

Record:

| Check | Result | Evidence |
|---|---|---|
| `./build_mac.sh` completed | PASS | GitHub Actions run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132), macOS job `83075924465`: `Build complete: dist/ReadOut.app`. |
| `dist/ReadOut.app` exists | PASS | macOS package smoke reported `App bundle exists PASS`; artifact `readout-macos-package-smoke` id `7835173905`, digest `sha256:0e9888702bbc65dbf766b3a7e0410cfb54197ef9c10eb3840beb4e28c8b545de`. |
| `tools/mac_package_smoke.sh` passed | PASS | macOS package smoke passed app launch, server ready, `/status`, `/voices`, `/history`, `/control`, and blocked-origin checks in run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132). |
| Menu-bar/tray icon visible | Pending manual | CI launched the packaged app but did not verify visible menu-bar/tray UI. |
| Tray `Open Control Panel` opens `/control` | Pending manual | CI verified packaged `/control` content, but did not select the tray/menu-bar item. |
| macOS preview/speak/stop lifecycle verified | Pending manual | CI smoke was non-audio; audible preview/speak/stop still needs manual evidence or accepted gap. |
| App quits cleanly | Pending manual | CI cleanup completed with a successful job, but the helper does not assert a post-quit process state. |

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
| `.\build_windows.ps1` completed | PASS | GitHub Actions run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132), Windows job `83075924486`: `Build complete: dist\ReadOut\ReadOut.exe`. |
| `dist\ReadOut\ReadOut.exe` exists | PASS | Windows package smoke reported `Executable exists PASS`; artifact `readout-windows-package-smoke` id `7835190908`, digest `sha256:7d13725b70c151c04c9b081e9881a3a44eacfb418b34730e93d092c4dbd5e3a4`. |
| `tools\windows_package_smoke.ps1` passed | PASS | Windows package smoke passed executable launch, server ready, non-audio server smoke, CORS origin matrix, and process stop checks in run [28061318132](https://github.com/DaveHomeAssist/readout/actions/runs/28061318132). |
| Server starts on `127.0.0.1:7778` | PASS | Windows package smoke reported `Server ready PASS` with `status=loading; engine=kokoro`. |
| `/control` opens and displays controls | PASS | Windows package smoke helper reported `GET /control PASS` with required controls present. |
| Windows preview/speak/stop lifecycle verified | Pending manual | CI smoke was headless and non-audio; audible preview/speak/stop still needs manual evidence or accepted gap. |
| App process stops cleanly | PASS | Windows package smoke reported `Stop packaged exe PASS` for pid `3172`. |

## Release Evidence Summary

| Item | Status | Notes |
|---|---|---|
| P3-A1 macOS packaging | Partial | Hosted build and non-audio package smoke passed; visible menu-bar/tray and audible lifecycle evidence remain pending. |
| P3-A2 Windows packaging | Partial | Hosted build, headless package smoke, `/control`, CORS, and stop checks passed; audible lifecycle evidence remains pending. |
| P3-A4 release checklist accepted | Pending | Architect acceptance is still required. |

## Known Acceptable Gaps

List any gap the Architect explicitly accepts for a release candidate.

| Gap | Accepted By | Date | Mitigation |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

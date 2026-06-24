# ReadOut Packaging Validation Worksheet

Last updated: 2026-06-23 21:07 -04:00

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
| `ARCHITECT_SIGNOFF.md` reviewed | PASS | Architect decisions are accepted in the Notion Architect sign-off page and transcribed in `ARCHITECT_SIGNOFF.md`; `tools/architect_signoff_check.ps1` is expected to pass. |
| `.\tools\release_preflight.ps1` or target equivalent run | PASS | Target-equivalent GitHub Actions package-smoke run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500) passed on package-producing commit `440cb577875dfd2aad8a359df972471e5c207511`; current Windows workstation also built and smoked `dist\ReadOut\ReadOut.exe` on 2026-06-23 21:07 -04:00; local full preflight remains blocked by manual evidence gates. |
| GitHub Actions `package-smoke` workflow run, if used | PASS | Run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500) passed; Windows job `83079089531` and macOS job `83079089516` both succeeded. |
| Python 3.10-3.12 confirmed | PASS | Tests workflow [28062313482](https://github.com/DaveHomeAssist/readout/actions/runs/28062313482) passed Python 3.10, 3.11, and 3.12 jobs on the package-producing commit; package-smoke used Python 3.12 on Windows and macOS. |
| `espeak-ng` confirmed on PATH | PASS | Package-smoke run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500) passed `Install espeak-ng` and package build steps on both Windows and macOS. Current local Windows build also passed with bundled `espeakng_loader` instead of system `espeak-ng` on PATH. |
| Full test suite run | PASS | Tests workflow [28062313482](https://github.com/DaveHomeAssist/readout/actions/runs/28062313482) passed on head `440cb577875dfd2aad8a359df972471e5c207511` for Python 3.10, 3.11, and 3.12. |

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
| `./build_mac.sh` completed | PASS | GitHub Actions run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500), macOS job `83079089516`: `Build complete: dist/ReadOut.app`. |
| `dist/ReadOut.app` exists | PASS | macOS package smoke reported `App bundle exists PASS`; artifact `readout-macos-package-smoke` id `7835539633`, digest `sha256:e47d55b52e30355d306099d40016eaeb43f7a10b942c44f141ae8cfc5f278758`. |
| `tools/mac_package_smoke.sh` passed | PASS | macOS package smoke passed app launch, server ready, `/status`, `/voices`, `/history`, `/control`, blocked-origin, and clean-quit checks in run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500). |
| Menu-bar/tray icon visible | Pending manual | CI launched the packaged app but did not verify visible menu-bar/tray UI. |
| Tray `Open Control Panel` opens `/control` | Pending manual | CI verified packaged `/control` content, but did not select the tray/menu-bar item. |
| macOS preview/speak/stop lifecycle verified | Pending manual | CI smoke was non-audio; audible preview/speak/stop still needs manual evidence or accepted gap. |
| App quits cleanly | PASS | macOS package smoke reported `App quits cleanly PASS` with no app process or server response after quit in run [28062313500](https://github.com/DaveHomeAssist/readout/actions/runs/28062313500). |

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
| `.\build_windows.ps1` completed | PASS | 2026-06-23 21:02 -04:00 local Windows build used Python 3.12.10 from `.venv`, installed `requirements.txt`, reported `espeak-ng: OK (bundled espeakng_loader)`, ran PyInstaller, and printed `Build complete: dist\ReadOut\ReadOut.exe`. |
| `dist\ReadOut\ReadOut.exe` exists | PASS | 2026-06-23 21:03 -04:00 local `Test-Path` confirmed `dist\ReadOut\ReadOut.exe`; file size was 66,886,685 bytes. |
| `tools\windows_package_smoke.ps1` passed | PASS | 2026-06-23 21:07 -04:00 local `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 120` passed executable launch, server ready, non-audio server smoke, CORS origin matrix, and process stop. |
| Server starts on `127.0.0.1:7778` | PASS | Local Windows package smoke reported `Server ready PASS` with `status=loading; engine=kokoro`; `GET /status` returned `dependency_issues=0`. |
| `/control` opens and displays controls | PASS | Local Windows package smoke helper reported `GET /control PASS` with required controls present. |
| Windows preview/speak/stop lifecycle verified | Pending manual | CI smoke was headless and non-audio; audible preview/speak/stop still needs manual evidence or accepted gap. |
| App process stops cleanly | PASS | Windows package smoke reported `Stop packaged exe PASS` for pid `4048`. |

## Release Evidence Summary

| Item | Status | Notes |
|---|---|---|
| P3-A1 macOS packaging | Partial | Hosted build, non-audio package smoke, and clean quit passed; visible menu-bar/tray and audible lifecycle evidence remain pending. |
| P3-A2 Windows packaging | Partial | Current local Windows build, headless package smoke, `/control`, CORS, and stop checks passed with bundled `espeakng_loader`; audible lifecycle evidence remains pending. |
| P3-A4 release checklist accepted | PASS | Architect accepted `RELEASE_CHECKLIST.md` as the reusable release gate; package/manual evidence rows still control final release readiness. |

## Known Acceptable Gaps

List any gap the Architect explicitly accepts for a release candidate.

| Gap | Accepted By | Date | Mitigation |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

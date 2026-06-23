# ReadOut Packaging Validation Worksheet

Last updated: 2026-06-23 15:31 -04:00

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
| `.\tools\release_preflight.ps1` or target equivalent run | PASS | Target-equivalent GitHub Actions package-smoke run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266) passed on `b2f02cee11ff6340ad5fcec51db4bb29e2856fdc`; local full preflight remains blocked by sign-off and manual evidence gates. |
| GitHub Actions `package-smoke` workflow run, if used | PASS | Run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266) passed; Windows job `83041801593` and macOS job `83041801690` both succeeded. |
| Python 3.10-3.12 confirmed | PASS | Tests workflow [28051156286](https://github.com/DaveHomeAssist/readout/actions/runs/28051156286) passed Python 3.10, 3.11, and 3.12 jobs; package-smoke used Python 3.12 on Windows and macOS. |
| `espeak-ng` confirmed on PATH | PASS | Package-smoke run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266) passed `Install espeak-ng` and package build steps on both Windows and macOS. |
| Full test suite run | PASS | Tests workflow [28051156286](https://github.com/DaveHomeAssist/readout/actions/runs/28051156286) passed on head `b2f02cee11ff6340ad5fcec51db4bb29e2856fdc` for Python 3.10, 3.11, and 3.12. |

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
| `./build_mac.sh` completed | PASS | GitHub Actions run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266), macOS job `83041801690`: `Build complete: dist/ReadOut.app`; app size `593M`. |
| `dist/ReadOut.app` exists | PASS | macOS package smoke reported `App bundle exists PASS`; artifact `readout-macos-package-smoke` id `7831229443`, digest `sha256:26bdd209799a0dd36eda66efcbd985d7b6a26c0c2c4242c6c66b37299462d335`. |
| `tools/mac_package_smoke.sh` passed | PASS | macOS package smoke passed app launch, server ready, `/status`, `/voices`, `/history`, `/control`, and blocked-origin checks in run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266). |
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
| `.\build_windows.ps1` completed | PASS | GitHub Actions run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266), Windows job `83041801593`: `Build complete: dist\ReadOut\ReadOut.exe`. |
| `dist\ReadOut\ReadOut.exe` exists | PASS | Windows package smoke reported `Executable exists PASS`; artifact `readout-windows-package-smoke` id `7831258309`, digest `sha256:6bfa7ce5974e8f13bdf335e4b1e967ea8efdff6dec04d213e3e4d2980a91f57d`. |
| `tools\windows_package_smoke.ps1` passed | PASS | Windows package smoke passed executable launch, server ready, non-audio server smoke, CORS origin matrix, and process stop checks in run [28051156266](https://github.com/DaveHomeAssist/readout/actions/runs/28051156266). |
| Server starts on `127.0.0.1:7778` | PASS | Windows package smoke reported `Server ready PASS` with `status=loading; engine=kokoro`. |
| `/control` opens and displays controls | PASS | Windows package smoke helper reported `GET /control PASS` with required controls present. |
| Windows preview/speak/stop lifecycle verified | Pending manual | CI smoke was headless and non-audio; audible preview/speak/stop still needs manual evidence or accepted gap. |
| App process stops cleanly | PASS | Windows package smoke reported `Stop packaged exe PASS` for pid `4048`. |

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

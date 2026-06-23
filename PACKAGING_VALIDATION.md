# ReadOut Packaging Validation Worksheet

Last updated: 2026-06-21 07:36 -04:00

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
| `ARCHITECT_SIGNOFF.md` reviewed | TBD | |
| `.\tools\release_preflight.ps1` or target equivalent run | TBD | |
| GitHub Actions `package-smoke` workflow run, if used | TBD | |
| Python 3.10-3.12 confirmed | TBD | |
| `espeak-ng` confirmed on PATH | TBD | |
| Full test suite run | TBD | |

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
| `./build_mac.sh` completed | TBD | |
| `dist/ReadOut.app` exists | TBD | |
| `tools/mac_package_smoke.sh` passed | TBD | |
| Menu-bar/tray icon visible | TBD | |
| Tray `Open Control Panel` opens `/control` | TBD | |
| macOS preview/speak/stop lifecycle verified | TBD | |
| App quits cleanly | TBD | |

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
| `.\build_windows.ps1` completed | TBD | |
| `dist\ReadOut\ReadOut.exe` exists | TBD | |
| `tools\windows_package_smoke.ps1` passed | TBD | |
| Server starts on `127.0.0.1:7778` | TBD | |
| `/control` opens and displays controls | TBD | |
| Windows preview/speak/stop lifecycle verified | TBD | |
| App process stops cleanly | TBD | |

## Release Evidence Summary

| Item | Status | Notes |
|---|---|---|
| P3-A1 macOS packaging | Pending | |
| P3-A2 Windows packaging | Pending | |
| P3-A4 release checklist accepted | Pending | |

## Known Acceptable Gaps

List any gap the Architect explicitly accepts for a release candidate.

| Gap | Accepted By | Date | Mitigation |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

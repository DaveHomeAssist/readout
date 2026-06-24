# ReadOut macOS Runner Handoff

Last updated: 2026-06-24

Use this packet when a macOS runner, hosted or local, is asked to refresh
ReadOut package evidence for branch `roadmap-integration`.

## Current Source Of Truth

- Repo: `DaveHomeAssist/readout`
- Branch: `roadmap-integration`
- Current verified head: `329095b`
- Latest tests workflow: `28076273743`, PASS on Python 3.10, 3.11, and 3.12
- Package evidence source: package-smoke run `28074903385`
- macOS package job: `83117008362`
- macOS artifact: `readout-macos-package-smoke`, id `7840118532`
- macOS artifact digest:
  `sha256:5868986c68411cd2ee7370a36835ecbcf2017c5335a72de9e9bf79124bcfd369`

Package evidence from run `28074903385` remains valid for current head
`329095b` because later commits only changed release-preflight reporting,
development smoke dependencies, tests, and milestone documentation. Rebuild
the package only when packaging/runtime source changes, when artifact freshness
is required for a release, or when Dave explicitly asks for a new macOS package
run.

## Do Not Reopen These As Blockers

These rows are already proven by hosted macOS package-smoke evidence unless the
package/runtime source has changed:

- Python 3.10-3.12 available on the macOS runner.
- `espeak-ng` installed and working on the macOS runner.
- `./build_mac.sh` produces `dist/ReadOut.app`.
- Packaged app launches and starts the server.
- `/control` opens and contains the primary macOS control surface.
- `/preview`, `/stop`, `/speak`, and final `/stop` lifecycle pass.
- Blocked browser origin is rejected.
- Menu-bar/tray icon is visible.
- Tray `Open Control Panel` opens `/control`.
- App quits cleanly.

## When To Run

Run macOS package smoke if any of these changed since the last package evidence:

- `main.py`, `server.py`, `ui.py`, `tts_engine.py`, `config.py`, or
  `dependency_check.py`
- `ReadOut.spec`
- `build_mac.sh`
- `requirements.txt`
- `assets/**`
- `engines/**`
- `tools/mac_package_smoke.sh`
- `.github/workflows/package-smoke.yml`

For documentation-only, test-only, or release-preflight-only changes, do not
rerun macOS packaging unless the release process requires exact-head package
artifacts.

## Hosted GitHub Runner Path

Preferred for repeatable evidence:

1. Open GitHub Actions for `DaveHomeAssist/readout`.
2. Run workflow `package-smoke` manually on branch `roadmap-integration`, or
   push a change that matches the workflow path filters.
3. Wait for job `macOS package smoke`.
4. Confirm the job command is:

```bash
./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui --evidence-dir macos-tray-evidence
```

5. Download or cite artifact `readout-macos-package-smoke`.
6. Record the run id, job id, artifact id, artifact digest, and pass/fail rows
   in `PACKAGING_VALIDATION.md`, `MILESTONE_LOG.md`, and any status run.

## Local macOS Runner Path

Run from repo root on macOS:

```bash
git status --short --branch
python3 --version
brew install espeak-ng || true
espeak-ng --version
chmod +x build_mac.sh tools/mac_package_smoke.sh
./build_mac.sh 2>&1 | tee build-macos.log
./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio --include-tray-ui --evidence-dir macos-tray-evidence 2>&1 | tee macos-package-smoke.md
tar -czf ReadOut-macOS.tar.gz -C dist ReadOut.app
```

Expected local artifacts:

- `ReadOut-macOS.tar.gz`
- `build-macos.log`
- `macos-package-smoke.md`
- `macos-tray-evidence/browser-control-url.txt`
- `macos-tray-evidence/readout-tray-menu-expanded.png`
- Any other `macos-tray-evidence/**` screenshots/logs produced by the helper

## Required PASS Rows

The smoke transcript must prove:

| Check | Required result |
|---|---|
| Launch packaged app | PASS |
| Server ready | PASS |
| GET `/status` | PASS |
| GET `/voices` | PASS |
| GET `/history` | PASS |
| GET `/control` | PASS |
| POST `/preview` | PASS |
| POST `/stop` after preview | PASS |
| POST `/speak` | PASS |
| POST `/stop` after speak | PASS |
| Menu-bar/tray icon visible | PASS |
| Tray `Open Control Panel` opens `/control` | PASS |
| Blocked origin | PASS |
| App quits cleanly | PASS |

If one of these rows fails, do not report GREEN. Report YELLOW if the failure is
an evidence gap and RED if the build, launch, server, audio lifecycle, CORS, or
quit behavior fails.

## Quick Triage

- Build fails before PyInstaller: check Python version, `espeak-ng`, and
  dependency install output in `build-macos.log`.
- App launches but `/status` never responds: check macOS app stdout/stderr in
  the smoke transcript and whether another process owns port `7778`.
- Audio lifecycle fails: inspect `/preview` or `/speak` response body and
  dependency issues in `/status`.
- Tray icon not found: verify the app is running as `ReadOut`, System Events is
  available, and the runner allows menu-bar UI automation.
- Tray click does not open `/control`: inspect
  `macos-tray-evidence/browser-control-url.txt` and the
  `READOUT_CONTROL_OPEN_PROBE` detail in `macos-package-smoke.md`.

## Status Report Template

```md
[light] ReadOut macOS package smoke -> [state], [short reason]

| Item | Light | Evidence | Gap | Next |
|---|---|---|---|---|
| macOS package smoke | [light] | run [id], job [id], artifact [id], digest [sha256], required rows [PASS/FAIL] | [none or rows] | [next action] |
```

Use GREEN only when the current macOS package evidence and current branch tests
are both verified.

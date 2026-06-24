# ReadOut Next Executor Prompt

Last updated: 2026-06-24

Use this prompt for the next executor assigned to verify or release the ReadOut
roadmap branch.

For macOS hosted/local package refreshes, also read `MAC_RUNNER_HANDOFF.md`.

```text
You are continuing ReadOut roadmap release validation on branch
`roadmap-integration` in repo `DaveHomeAssist/readout`.

Do not reopen the old packaging prerequisite loop. Hosted and local evidence
already proves Python 3.10-3.12, `espeak-ng`, Windows package build, macOS
package build, Windows package audio lifecycle, macOS package audio lifecycle,
macOS tray/menu UI, and manual smoke:

- GitHub Actions package-smoke run `28074903385` passed on commit `10d7550`.
- macOS job `83117008362` built `dist/ReadOut.app`, passed packaged app
  launch, server, `/status`, `/voices`, `/history`, `/control`, blocked-origin,
  clean quit, and audio lifecycle via `./tools/mac_package_smoke.sh --app
  dist/ReadOut.app --include-audio --include-tray-ui --evidence-dir
  macos-tray-evidence`: `/preview status=playing`, `/stop status=stopped`,
  `/speak status=playing`, `/stop status=stopped`.
- The same macOS run passed `Menu-bar/tray icon visible` by locating the
  ReadOut status menu through System Events and saving screenshots in
  `macos-tray-evidence`.
- The same macOS run passed tray `Open Control Panel` to `/control`; the tray
  click launched a browser process with callback target
  `http://127.0.0.1:7778/control`.
- macOS artifact `readout-macos-package-smoke` id `7840118532` has digest
  `sha256:5868986c68411cd2ee7370a36835ecbcf2017c5335a72de9e9bf79124bcfd369`.
- Windows job `83117008329` built `dist\ReadOut\ReadOut.exe`, passed server,
  `/control`, CORS, and process-stop checks, and uploaded artifact
  `readout-windows-package-smoke` id `7840090908` with digest
  `sha256:d8cadd4e45240e21eb31806b19ef499b99d5ad4e066bdaa08b155cacbacd7894`.
- Tests workflow run `28062313482` passed Python 3.10, 3.11, and 3.12 jobs on
  the earlier package-producing commit. If branch head has advanced, re-query
  the latest tests workflow before reporting final green.
- Current local Windows evidence includes audio endpoint lifecycle:
  `.\build_windows.ps1` completed on 2026-06-23 with Python 3.12.10, bundled
  `espeakng_loader`, bundled Kokoro source files, bundled `en_core_web_sm`,
  Torch pinned below the frozen-runtime regression, and core VC runtime DLLs
  forced from `System32`, producing `dist\ReadOut\ReadOut.exe`.
  `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe
  -TimeoutSec 240 -IncludeAudio` passed with `dependency_issues=0`, including
  `/preview status=playing`, `/speak status=playing`, and `/stop status=stopped`.
- Current manual smoke evidence passes:
  `.\tools\manual_smoke_check.ps1` passes after refreshed source `/control`,
  Tk desktop, and Chrome extension runtime evidence. `.\tools\control_browser_action_smoke.ps1
  -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` clicked rendered
  Preview, Speak, Save WAV, and Stop controls. `.\tools\tk_desktop_runtime_smoke.ps1
  -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` opened the real Tk UI
  and exercised Preview, Speak, Save WAV, and Stop. `.\tools\extension_runtime_smoke.ps1
  -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` loaded the unpacked
  extension through Chromium DevTools, verified popup OFFLINE/READY, allowlisted
  the real extension origin, clicked popup Preview, invoked the service-worker
  context-menu selected-text handler, ran Stop, and restored local
  config/history. Chrome did not expose a tab target for
  `Extensions.triggerAction`, so the helper used its DevTools-loaded popup
  fallback and direct service-worker handler invocation.

Later documentation/test-only commits may advance the branch head without
invalidating package artifacts. Rerun package-smoke only if package/runtime
source changes or the release process requires artifacts from the exact final
commit.

First verify current state:

1. Run `git status --short --branch`.
2. Run `.\tools\upstream_reconciliation.ps1`.
3. Run `.\tools\roadmap_audit.ps1`.
4. Run `.\tools\packaging_validation_check.ps1`.
5. Run `.\tools\manual_smoke_check.ps1`.
6. Run `.\tools\architect_signoff_check.ps1`.
7. Run `python -m pytest`.
8. Run `.\tools\secret_scan.ps1`.
9. Run `.\tools\release_preflight.ps1`.
10. Run `git diff --check`.

Expected current state is GREEN only if those current checks pass and the latest
queried GitHub test/package runs are not red. Do not infer green from this file
alone.

Final release gate:

- Confirm `PACKAGING_VALIDATION.md` still records P3-A1 and P3-A2 as PASS.
- Confirm `MANUAL_SMOKE_VALIDATION.md` still passes.
- Confirm `ROADMAP_STATUS.md` has no intentionally open roadmap gates.
- Re-run live/source checks if source, control UI, Tk UI, or extension code has
  changed since the last smoke evidence:
  `.\tools\control_browser_runtime_smoke.ps1`,
  `.\tools\control_browser_action_smoke.ps1 -TimeoutSec 180`,
  `.\tools\tk_desktop_static_smoke.ps1`,
  `.\tools\tk_desktop_runtime_smoke.ps1 -TimeoutSec 180`,
  `.\tools\extension_runtime_smoke.ps1 -TimeoutSec 180`, then
  `.\tools\manual_smoke_check.ps1`.
- Re-run package-smoke if packaging/runtime source changes.

Status reporting rules:

- Use traffic light output.
- Report GREEN only after `roadmap_audit.ps1`, `architect_signoff_check.ps1`,
  `packaging_validation_check.ps1`, `manual_smoke_check.ps1`,
  `upstream_reconciliation.ps1`, `release_preflight.ps1`, tests, secret scan,
  and diff check all pass.
- Report YELLOW if a current check is incomplete or the latest GitHub tests are
  unconfirmed.
- Report RED for failed builds, failed tests, failed smoke tests, or rejected
  Architect rows.
- Report GREY only if the repo, GitHub run evidence, or worksheets cannot be
  reached.

Do not install Python or `espeak-ng` on Dave's workstation unless the current
task is explicitly to build packages locally on that workstation. Use the
recorded hosted package-smoke evidence as the package prerequisite source of
truth. Do not list Python 3.10-3.12, `espeak-ng`, `Menu-bar/tray icon visible`,
or tray `Open Control Panel` as open blockers for this branch unless
package/runtime source changes invalidate the recorded hosted evidence or the
user explicitly asks for local workstation packaging.
```

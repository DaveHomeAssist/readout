# ReadOut Next Executor Prompt

Last updated: 2026-06-24

Use this prompt for the next executor assigned to finish the ReadOut roadmap
release gates.

```text
You are continuing ReadOut roadmap release validation on branch
`roadmap-integration` in repo `DaveHomeAssist/readout`.

Do not restart the old packaging prerequisite loop. Hosted and local evidence
already proves Python 3.10-3.12, `espeak-ng`, Windows package build, macOS
package build, Windows package audio lifecycle, macOS package audio lifecycle,
and manual smoke:

- GitHub Actions package-smoke run `28073664040` passed on commit `999cb7f`.
- macOS job `83113369649` built `dist/ReadOut.app`, passed packaged app launch,
  server, `/status`, `/voices`, `/history`, `/control`, blocked-origin, clean
  quit, and audio lifecycle via `./tools/mac_package_smoke.sh --app
  dist/ReadOut.app --include-audio`: `/preview status=playing`,
  `/stop status=stopped`, `/speak status=playing`, `/stop status=stopped`.
  It uploaded artifact `readout-macos-package-smoke` id `7839652216`.
- Windows job `83113369684` built `dist\ReadOut\ReadOut.exe`, passed server,
  `/control`, CORS, and process-stop checks, and uploaded artifact
  `readout-windows-package-smoke` id `7839666877`.
- Earlier GitHub Actions package-smoke run `28062313500` passed on package-producing commit
  `440cb577875dfd2aad8a359df972471e5c207511` and remains supporting
  prerequisite history.
- Windows job `83079089531` built `dist\ReadOut\ReadOut.exe`, passed server,
  `/control`, CORS, and process-stop checks, and uploaded artifact
  `readout-windows-package-smoke` id `7835571251`.
- macOS job `83079089516` built `dist/ReadOut.app`, passed packaged app launch,
  server, `/status`, `/voices`, `/history`, `/control`, and blocked-origin
  checks, verified clean quit, and uploaded artifact
  `readout-macos-package-smoke` id `7835539633`.
- Tests workflow run `28062313482` passed Python 3.10, 3.11, and 3.12 jobs on
  the same package-producing commit.
- Current local Windows evidence now includes audio endpoint lifecycle:
  `.\build_windows.ps1` completed on 2026-06-23 with Python 3.12.10, bundled
  `espeakng_loader`, bundled Kokoro source files, bundled `en_core_web_sm`,
  Torch pinned below the frozen-runtime regression, and core VC runtime DLLs
  forced from `System32`, producing `dist\ReadOut\ReadOut.exe`.
  `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe
  -TimeoutSec 240 -IncludeAudio` passed with `dependency_issues=0`, including
  `/preview status=playing`, `/speak status=playing`, and `/stop status=stopped`.
- Current manual smoke evidence now passes:
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

Later documentation-only commits may advance the branch head without
invalidating that package evidence. Rerun package-smoke if package/runtime
source changes or the release process requires artifacts from the exact final
commit.

Current branch work after `8ae9c48` adds a stronger macOS package-smoke mode:
`./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio
--include-tray-ui --evidence-dir macos-tray-evidence`. The workflow should run
that command and upload `macos-tray-evidence/**`. Use that artifact first for
the two visual tray rows. Fall back to a human macOS target check or explicit
accepted gaps only if the runner cannot drive System Events/menu-bar UI.

First verify current state:

1. Run `git status --short --branch`.
2. Run `.\tools\upstream_reconciliation.ps1`.
3. Run `.\tools\roadmap_audit.ps1`.
4. Run `.\tools\packaging_validation_check.ps1`.
5. Run `.\tools\manual_smoke_check.ps1`.
6. Run `.\tools\architect_signoff_check.ps1`.

Expected current state is YELLOW, not GREEN:

- `roadmap_audit.ps1` should pass roadmap coverage, upstream graph,
  Python 3.10-3.12, `espeak-ng`, Architect sign-off, and manual smoke.
- It should still fail packaging validation until the macOS visual rows below are
  completed or accepted as gaps.

Finish these open rows:

1. `PACKAGING_VALIDATION.md`
   - macOS: verify `Menu-bar/tray icon visible`; prefer
     `--include-tray-ui` evidence from the latest package-smoke run.
   - macOS: verify tray `Open Control Panel` opens `/control`; prefer the
     `READOUT_CONTROL_OPEN_PROBE` log from `macos-tray-evidence`.
   - Run `.\tools\packaging_validation_check.ps1`.

2. `MANUAL_SMOKE_VALIDATION.md`
   - Manual smoke is currently complete with automated runtime evidence.
   - Refresh it if source/control/Tk/extension code changes:
     `.\tools\control_browser_runtime_smoke.ps1`,
     `.\tools\control_browser_action_smoke.ps1 -TimeoutSec 180`,
     `.\tools\tk_desktop_runtime_smoke.ps1 -TimeoutSec 180`,
     `.\tools\extension_runtime_smoke.ps1 -TimeoutSec 180`, then
     `.\tools\manual_smoke_check.ps1`.

3. Final release gate
   - Run `python -m pytest`.
   - Run `.\tools\secret_scan.ps1`.
   - Confirm `.\tools\release_preflight.ps1` reports `Upstream reconciliation`
     `Extension static smoke`, and `Tk desktop static smoke` as PASS.
   - With ReadOut running, run `.\tools\control_workflow_smoke.ps1`.
   - Run `.\tools\control_browser_runtime_smoke.ps1`.
   - Run `.\tools\control_browser_action_smoke.ps1`.
   - Run `.\tools\extension_runtime_smoke.ps1`.
   - Run `.\tools\release_preflight.ps1`.
   - Run `git diff --check`.
   - Update `MILESTONE_LOG.md`, `ROADMAP_STATUS.md`, and any worksheet rows with
     exact evidence.

Status reporting rules:

- Use traffic light output.
- Report GREEN only after `roadmap_audit.ps1`, `architect_signoff_check.ps1`,
  `packaging_validation_check.ps1`, `manual_smoke_check.ps1`,
  `upstream_reconciliation.ps1`, `release_preflight.ps1`, tests, secret scan,
  and diff check all pass.
- Report YELLOW while any manual/package row is incomplete but progress is
  recorded.
- Report RED for failed builds, failed smoke tests, or rejected Architect rows.
- Report GREY only if the repo, GitHub run evidence, or worksheets cannot be
  reached.

Do not install Python or `espeak-ng` on Dave's workstation unless the current
task is explicitly to build packages locally on that workstation. Use the
recorded hosted package-smoke evidence as the package prerequisite source of
truth. Do not list Python 3.10-3.12 or `espeak-ng` as open blockers for this
branch unless package/runtime source changes invalidate the recorded hosted
evidence or the user explicitly asks for local workstation packaging.
```

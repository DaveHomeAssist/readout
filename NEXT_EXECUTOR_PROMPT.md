# ReadOut Next Executor Prompt

Last updated: 2026-06-23 19:23 -04:00

Use this prompt for the next executor assigned to finish the ReadOut roadmap
release gates.

```text
You are continuing ReadOut roadmap release validation on branch
`roadmap-integration` in repo `DaveHomeAssist/readout`.

Do not restart the old packaging prerequisite loop. Hosted evidence already
proves Python 3.10-3.12, `espeak-ng`, Windows package build, macOS package
build, and non-audio package smoke:

- GitHub Actions package-smoke run `28062313500` passed on package-producing commit
  `440cb577875dfd2aad8a359df972471e5c207511`.
- Windows job `83079089531` built `dist\ReadOut\ReadOut.exe`, passed server,
  `/control`, CORS, and process-stop checks, and uploaded artifact
  `readout-windows-package-smoke` id `7835571251`.
- macOS job `83079089516` built `dist/ReadOut.app`, passed packaged app launch,
  server, `/status`, `/voices`, `/history`, `/control`, and blocked-origin
  checks, verified clean quit, and uploaded artifact
  `readout-macos-package-smoke` id `7835539633`.
- Tests workflow run `28062313482` passed Python 3.10, 3.11, and 3.12 jobs on
  the same package-producing commit.

Later documentation-only commits may advance the branch head without
invalidating that package evidence. Rerun package-smoke only if package/runtime
source changes or the release process requires artifacts from the exact final
commit.

First verify current state:

1. Run `git status --short --branch`.
2. Run `.\tools\upstream_reconciliation.ps1`.
3. Run `.\tools\roadmap_audit.ps1`.
4. Run `.\tools\packaging_validation_check.ps1`.
5. Run `.\tools\manual_smoke_check.ps1`.
6. Run `.\tools\architect_signoff_check.ps1`.

Expected current state is YELLOW, not GREEN:

- `roadmap_audit.ps1` should pass roadmap coverage, upstream graph,
  Python 3.10-3.12, `espeak-ng`, and Architect sign-off.
- It should still fail packaging validation and manual smoke validation until
  the rows below are completed or accepted as gaps.

Finish these open rows:

1. `PACKAGING_VALIDATION.md`
   - macOS: verify `Menu-bar/tray icon visible`.
   - macOS: verify tray `Open Control Panel` opens `/control`.
   - macOS: verify audible preview/speak/stop lifecycle.
   - Windows: verify audible preview/speak/stop lifecycle, or record an
     accepted gap.
   - Run `.\tools\packaging_validation_check.ps1`.

2. `MANUAL_SMOKE_VALIDATION.md`
   - Fill source `/control` manual smoke rows.
   - Fill Tk desktop smoke rows.
   - Fill Chrome extension smoke rows.
   - Run `.\tools\manual_smoke_check.ps1`.

3. Final release gate
   - Run `python -m pytest`.
   - Run `.\tools\secret_scan.ps1`.
   - Confirm `.\tools\release_preflight.ps1` reports `Upstream reconciliation`
     `Extension static smoke`, and `Tk desktop static smoke` as PASS.
   - With ReadOut running, run `.\tools\control_workflow_smoke.ps1`.
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

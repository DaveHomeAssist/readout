# ReadOut Roadmap Status

Last updated: 2026-06-23 19:12 -04:00

This is the current requirement-by-requirement audit for the roadmap. It does
not replace `MILESTONE_LOG.md`; it is the short release-readiness view. Run
`tools/roadmap_audit.ps1` for a live local summary of the remaining gate state.

## Status Legend
- **Complete:** Current evidence satisfies the done condition.
- **Drafted:** Artifact exists, but owner acceptance/sign-off is still missing.
- **Preflight hardened:** Scripts/checks are improved, but target validation is still missing.
- **Pending external validation:** Requires a target machine, runtime dependency, or owner sign-off.

## Current Integration Risk

The roadmap work has been moved to a clean `roadmap-integration` worktree based
on `origin/main`, clearing the upstream graph blocker for this branch. The
integration keeps upstream engine registry, unified `/voices` catalogue
consumption, control-panel redesign, startup-race hardening, config-file
permission hardening, least-privilege extension manifest, disabled FastAPI
docs/OpenAPI, and loopback Host guard, then layers on the roadmap requirements:
exact trusted browser origins through `allowed_origins` /
`READOUT_ALLOWED_ORIGINS`, `/preview`, local opt-in history, dependency checks,
release preflight, and packaging-validation artifacts. The original dirty local
`main` worktree remains a safety copy and should not be blindly pulled over.
Use `UPSTREAM_RECONCILIATION.md`, `tools/upstream_reconciliation.ps1`, and the
`Upstream reconciliation` row in `tools/release_preflight.ps1` for review
context.

## Phase 0 - Security Stabilization

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P0-A1 | Complete | Exact-origin CORS regression tests; live source HTTP CORS matrix; live source HTTP origin-rejection before `/speak` side effects; loopback Host guard tests; docs/OpenAPI disabled tests; `tools/cors_origin_matrix.ps1`; milestone curl matrix | Run live matrix again during release gate |
| P0-A2 | Complete | `/config` regression tests and live source HTTP `/config` response prove OpenAI and ElevenLabs keys are redacted from responses while remaining on disk | None |
| P0-A3 | Complete | API regression tests and live source HTTP smoke cover `/config`, `/speak`, `/stop`, `/status`, `/voices`, `/history`, `/control`, and `/preview` success/failure paths; `tools/release_preflight.ps1 -RunSourceSmoke` runs the source smoke gate explicitly | Re-run full suite before release |
| P0-A4 | Complete | `THREAT_MODEL.md`; `DECISION_LOG.md` P0-A4 entry; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance; `tools/architect_signoff_check.ps1` gate | None |

## Phase 1 - UI Truthfulness and Cleanup

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P1-A1 | Complete | UI/docs copy tests block `Save MP3` and require `Save WAV` | None |
| P1-A2 | Complete | Browser engine tab removed; unsupported `engine: browser` rejected; decision logged; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |
| P1-A3 | Complete | Desktop methods PATCH engine/voice/speed payloads; status polling restores persisted engine/voice/speed without repatching; `tools/tk_desktop_static_smoke.ps1` verifies Tk desktop control and endpoint wiring without launching a GUI; `tools/tk_desktop_runtime_smoke.ps1` opens the real Tk window on Windows and verifies engine/voice/speed persistence through backend `/status` while restoring local config/history; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate remaining audio evidence | Manual desktop audio smoke before release |
| P1-A4 | Complete | Auto-read control removed; decision logged; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |
| P1-A5 | Complete | Queue download buttons removed; decision logged; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Phase 2 - Control Surface Polish

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P2-A1 | Complete | macOS routes to `/control` by default; docs and `/control` copy agree; control workflows present; live source HTTP smoke verifies `/control`; `tools/server_smoke.ps1` checks `/control` without audio; `tools/control_workflow_smoke.ps1` verifies status refresh, history controls, and stop backend without audio; `tools/control_browser_runtime_smoke.ps1` verifies the browser-rendered `/control` status display updates from `/status`; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | macOS packaged tray-to-control-panel smoke remains a P3-A1 packaging validation row |
| P2-A2 | Complete | Extension popup status/error source tests cover READY, LOADING, OFFLINE, failures, next-action text, preview controls, and registry-sourced `/voices` catalogue loading; `tools/extension_static_smoke.ps1` verifies Manifest V3, permissions, endpoint wiring, context menu IDs, and toast contract; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate target smoke evidence | Chrome popup runtime smoke before release |
| P2-A3 | Complete | `/preview` API tests; live source HTTP preview smoke; desktop/control/popup source tests; preview does not mutate config, save audio, or add history; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate audible preview evidence | Manual audio preview smoke before release |
| P2-A4 | Complete | Local history is off by default, capped, clearable, and documented; decision logged; `tools/control_workflow_smoke.ps1` verifies history enable/limit, status refresh, clear, and local config/history restore; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Phase 3 - Packaging and Distribution

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P3-A1 | Partial hosted validation, pending manual macOS smoke | `build_mac.sh` checks supported Python and `espeak-ng`; build-script tests cover preflight expectations; packaged entrypoint tests prove tray/control-panel routing; GitHub Actions package-smoke run `28062313500` built `dist/ReadOut.app` at package-producing commit `440cb577875dfd2aad8a359df972471e5c207511`, passed `tools/mac_package_smoke.sh`, verified clean quit, and uploaded artifact `7835539633`; `PACKAGING_VALIDATION.md` captures results; `tools/packaging_validation_check.ps1` still fails until manual rows are passed or accepted as gaps | Manually verify menu-bar/tray icon, tray `Open Control Panel`, and audible preview/speak/stop, or record accepted gaps |
| P3-A2 | Partial hosted validation, pending manual Windows audio smoke | `build_windows.ps1` avoids broken Python shims, checks supported Python and `espeak-ng`; GitHub Actions package-smoke run `28062313500` built `dist\ReadOut\ReadOut.exe` at package-producing commit `440cb577875dfd2aad8a359df972471e5c207511`, passed headless `tools/windows_package_smoke.ps1`, verified `/control` and CORS, stopped the exe, and uploaded artifact `7835571251`; `PACKAGING_VALIDATION.md` captures results; `tools/packaging_validation_check.ps1` still fails until manual audio rows are passed or accepted as gaps | Manually verify Windows audible preview/speak/stop lifecycle or record an accepted gap |
| P3-A3 | Complete | Dependency checks expose Python/Kokoro/espeak-ng issues in startup, `/status`, popup, and `/control`; tests cover pass/fail states | Clean-machine smoke before release |
| P3-A4 | Complete | `RELEASE_CHECKLIST.md`; release-doc tests; `tools/release_preflight.ps1 -RunSourceSmoke`; `tools/architect_signoff_check.ps1` with behavioral pass/fail fixture tests; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Current Blocking Conditions
- Architect sign-off/review has been transcribed from the Notion Architect page; rerun `tools/architect_signoff_check.ps1` before release to confirm it remains PASS.
- Upstream graph reconciliation is cleared in the `roadmap-integration` worktree; rerun `tools/upstream_reconciliation.ps1`, `tools/roadmap_audit.ps1`, and `tools/release_preflight.ps1` before release to confirm `behind=0` and preflight `Upstream reconciliation` PASS.
- Hosted macOS package build, non-audio smoke, and clean-quit evidence exists, but visible menu-bar/tray and audible lifecycle evidence remain pending; final release should pass `tools/packaging_validation_check.ps1`.
- Hosted Windows package build and headless non-audio smoke evidence exists, but audible preview/speak/stop evidence remains pending; final release should pass `tools/packaging_validation_check.ps1`.
- Manual smoke tests remain for Tk desktop audio, Chrome extension popup/runtime, `/control` audio rows, packaged macOS lifecycle, and packaged Windows lifecycle. Use `tools/release_preflight.ps1 -RunSourceSmoke` first, `tools/server_smoke.ps1` for non-audio API/control checks, `tools/control_browser_runtime_smoke.ps1` for browser-rendered `/control` status evidence, `tools/tk_desktop_static_smoke.ps1` for Tk source-contract support evidence, `tools/tk_desktop_runtime_smoke.ps1` for non-audio Tk launch/config evidence, and `tools/manual_smoke_check.ps1` after filling interactive smoke evidence.

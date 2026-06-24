# ReadOut Roadmap Status

Last updated: 2026-06-23 23:22 -04:00

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
| P1-A3 | Complete | Desktop methods PATCH engine/voice/speed payloads; status polling restores persisted engine/voice/speed without repatching; `tools/tk_desktop_static_smoke.ps1` verifies Tk desktop control and endpoint wiring without launching a GUI; `tools/tk_desktop_runtime_smoke.ps1` opens the real Tk window on Windows, verifies engine/voice/speed persistence, exercises Preview/Speak/Save WAV/Stop through the desktop methods, removes the generated WAV, and restores local config/history; `MANUAL_SMOKE_VALIDATION.md` passes | None |
| P1-A4 | Complete | Auto-read control removed; decision logged; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |
| P1-A5 | Complete | Queue download buttons removed; decision logged; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Phase 2 - Control Surface Polish

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P2-A1 | Complete | macOS routes to `/control` by default; docs and `/control` copy agree; control workflows present; live source HTTP smoke verifies `/control`; `tools/server_smoke.ps1` checks `/control` with optional preview/speak/stop lifecycle; `tools/control_workflow_smoke.ps1` verifies status refresh, history controls, and stop backend; `tools/control_browser_runtime_smoke.ps1` verifies the browser-rendered `/control` status display updates from `/status`; `tools/control_browser_action_smoke.ps1` clicks rendered Preview, Speak, Save WAV, and Stop controls, verifies a WAV is created, and restores config/history; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | macOS packaged tray-to-control-panel smoke remains a P3-A1 packaging validation row |
| P2-A2 | Complete | Extension popup status/error source tests cover READY, LOADING, OFFLINE, failures, next-action text, preview controls, and registry-sourced `/voices` catalogue loading; `tools/extension_static_smoke.ps1` verifies Manifest V3, permissions, endpoint wiring, context menu IDs, and toast contract; `tools/extension_runtime_smoke.ps1` loads the unpacked extension through Chromium DevTools, verifies OFFLINE/READY popup text, allowlists the real extension origin, clicks popup Preview, invokes the service-worker context-menu selected-text handler, and runs the shared Stop command path while restoring local config/history | None |
| P2-A3 | Complete | `/preview` API tests; live source HTTP preview smoke; desktop/control/popup source tests; preview does not mutate config, save audio, or add history; `tools/control_browser_action_smoke.ps1`, `tools/tk_desktop_runtime_smoke.ps1`, `tools/extension_runtime_smoke.ps1`, `MANUAL_SMOKE_VALIDATION.md`, and `tools/manual_smoke_check.ps1` now cover preview playback lifecycle evidence | None |
| P2-A4 | Complete | Local history is off by default, capped, clearable, and documented; decision logged; `tools/control_workflow_smoke.ps1` verifies history enable/limit, status refresh, clear, and local config/history restore; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Phase 3 - Packaging and Distribution

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P3-A1 | Partial hosted validation, pending manual macOS visual smoke | `build_mac.sh` checks supported Python and `espeak-ng`; build-script tests cover preflight expectations; packaged entrypoint tests prove tray/control-panel routing; GitHub Actions package-smoke run `28073664040` built `dist/ReadOut.app`, passed `tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio`, verified `/control`, preview/stop/speak/stop audio lifecycle, blocked-origin, clean quit, and uploaded artifact `7839652216`; `PACKAGING_VALIDATION.md` captures results; `tools/packaging_validation_check.ps1` still fails until visual tray/menu rows are passed or accepted as gaps | Manually verify menu-bar/tray icon and tray `Open Control Panel`, or record accepted gaps |
| P3-A2 | Complete local Windows validation | `build_windows.ps1` avoids broken Python shims, accepts system `espeak-ng` or bundled `espeakng_loader`, pins Torch below the frozen-runtime regression, bundles Kokoro source and `en_core_web_sm`, forces core VC runtime DLLs from `System32`, and built `dist\ReadOut\ReadOut.exe` locally on 2026-06-23 with Python 3.12.10; `tools/windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 240 -IncludeAudio` passed executable launch, server ready, `/control`, preview, speak, stop, CORS, dependency issues 0, and process stop; `PACKAGING_VALIDATION.md` captures results | None |
| P3-A3 | Complete | Dependency checks expose Python/Kokoro/eSpeak runtime issues in startup, `/status`, popup, and `/control`; checks accept either system `espeak-ng` or bundled `espeakng_loader`; tests cover pass/fail states | Clean-machine smoke before release |
| P3-A4 | Complete | `RELEASE_CHECKLIST.md`; release-doc tests; `tools/release_preflight.ps1 -RunSourceSmoke`; `tools/architect_signoff_check.ps1` with behavioral pass/fail fixture tests; Notion Architect sign-off page; `ARCHITECT_SIGNOFF.md` transcribed acceptance | None |

## Current Blocking Conditions
- Architect sign-off/review has been transcribed from the Notion Architect page; rerun `tools/architect_signoff_check.ps1` before release to confirm it remains PASS.
- Upstream graph reconciliation is cleared in the `roadmap-integration` worktree; rerun `tools/upstream_reconciliation.ps1`, `tools/roadmap_audit.ps1`, and `tools/release_preflight.ps1` before release to confirm `behind=0` and preflight `Upstream reconciliation` PASS.
- Hosted macOS package build, `/control`, audio lifecycle, blocked-origin, and clean-quit evidence now exists from package-smoke run `28073664040`, but visible menu-bar/tray and tray menu selection still require macOS target evidence or accepted gaps; final release should pass `tools/packaging_validation_check.ps1`.
- Current local Windows package build and package audio endpoint smoke evidence passes; final packaging validation remains blocked by macOS visible tray/menu-bar and tray Open Control Panel rows.
- Manual smoke validation now passes with automated runtime evidence for source `/control`, Tk desktop, and Chrome extension paths. Use `tools/release_preflight.ps1 -RunSourceSmoke`, `tools/server_smoke.ps1 -IncludeAudio`, `tools/control_browser_runtime_smoke.ps1`, `tools/control_browser_action_smoke.ps1`, `tools/extension_runtime_smoke.ps1`, `tools/tk_desktop_static_smoke.ps1`, `tools/tk_desktop_runtime_smoke.ps1`, and `tools/manual_smoke_check.ps1` to refresh that evidence before release. The remaining release blocker is packaged macOS tray/control/audio validation.

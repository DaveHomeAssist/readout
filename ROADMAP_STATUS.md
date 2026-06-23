# ReadOut Roadmap Status

Last updated: 2026-06-23 15:31 -04:00

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
Use `UPSTREAM_RECONCILIATION.md` and `tools/upstream_reconciliation.ps1` for
review context.

## Phase 0 - Security Stabilization

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P0-A1 | Complete | Exact-origin CORS regression tests; live source HTTP CORS matrix; live source HTTP origin-rejection before `/speak` side effects; loopback Host guard tests; docs/OpenAPI disabled tests; `tools/cors_origin_matrix.ps1`; milestone curl matrix | Run live matrix again during release gate |
| P0-A2 | Complete | `/config` regression tests and live source HTTP `/config` response prove OpenAI and ElevenLabs keys are redacted from responses while remaining on disk | None |
| P0-A3 | Complete | API regression tests and live source HTTP smoke cover `/config`, `/speak`, `/stop`, `/status`, `/voices`, `/history`, `/control`, and `/preview` success/failure paths; `tools/release_preflight.ps1 -RunSourceSmoke` runs the source smoke gate explicitly | Re-run full suite before release |
| P0-A4 | Drafted, pending Architect sign-off | `THREAT_MODEL.md`; `DECISION_LOG.md` P0-A4 entry; `ARCHITECT_SIGNOFF.md` packet; `tools/architect_signoff_check.ps1` gate | Architect sign-off |

## Phase 1 - UI Truthfulness and Cleanup

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P1-A1 | Complete | UI/docs copy tests block `Save MP3` and require `Save WAV` | None |
| P1-A2 | Complete, pending Architect review | Browser engine tab removed; unsupported `engine: browser` rejected; decision logged; `ARCHITECT_SIGNOFF.md` packet | Architect review |
| P1-A3 | Complete | Desktop methods PATCH engine/voice/speed payloads; status polling restores persisted engine/voice/speed without repatching; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate target smoke evidence | Manual desktop smoke before release |
| P1-A4 | Complete, pending Architect review | Auto-read control removed; decision logged; `ARCHITECT_SIGNOFF.md` packet | Architect review |
| P1-A5 | Complete, pending Architect review | Queue download buttons removed; decision logged; `ARCHITECT_SIGNOFF.md` packet | Architect review |

## Phase 2 - Control Surface Polish

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P2-A1 | Complete, pending Architect review | macOS routes to `/control` by default; docs and `/control` copy agree; control workflows present; live source HTTP smoke verifies `/control`; `tools/server_smoke.ps1` checks `/control` without audio; `ARCHITECT_SIGNOFF.md` packet | macOS tray-to-control-panel smoke; Architect review |
| P2-A2 | Complete | Extension popup status/error source tests cover READY, LOADING, OFFLINE, failures, next-action text, preview controls, and registry-sourced `/voices` catalogue loading; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate target smoke evidence | Chrome popup smoke before release |
| P2-A3 | Complete | `/preview` API tests; live source HTTP preview smoke; desktop/control/popup source tests; preview does not mutate config, save audio, or add history; `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1` gate audible preview evidence | Manual audio preview smoke before release |
| P2-A4 | Complete, pending Architect review | Local history is off by default, capped, clearable, and documented; decision logged; `ARCHITECT_SIGNOFF.md` packet | Architect review |

## Phase 3 - Packaging and Distribution

| ID | Status | Current Evidence | Remaining Proof |
|---|---|---|---|
| P3-A1 | Partial hosted validation, pending manual macOS smoke | `build_mac.sh` checks supported Python and `espeak-ng`; build-script tests cover preflight expectations; packaged entrypoint tests prove tray/control-panel routing; GitHub Actions package-smoke run `28051156266` built `dist/ReadOut.app`, passed `tools/mac_package_smoke.sh`, and uploaded artifact `7831229443`; `PACKAGING_VALIDATION.md` captures results; `tools/packaging_validation_check.ps1` still fails until manual rows are passed or accepted as gaps | Manually verify menu-bar/tray icon, tray `Open Control Panel`, audible preview/speak/stop, and clean quit or record accepted gaps |
| P3-A2 | Partial hosted validation, pending manual Windows audio smoke | `build_windows.ps1` avoids broken Python shims, checks supported Python and `espeak-ng`; GitHub Actions package-smoke run `28051156266` built `dist\ReadOut\ReadOut.exe`, passed headless `tools/windows_package_smoke.ps1`, verified `/control` and CORS, stopped the exe, and uploaded artifact `7831258309`; `PACKAGING_VALIDATION.md` captures results; `tools/packaging_validation_check.ps1` still fails until manual audio rows are passed or accepted as gaps | Manually verify Windows audible preview/speak/stop lifecycle or record an accepted gap |
| P3-A3 | Complete | Dependency checks expose Python/Kokoro/espeak-ng issues in startup, `/status`, popup, and `/control`; tests cover pass/fail states | Clean-machine smoke before release |
| P3-A4 | Drafted, pending Architect acceptance | `RELEASE_CHECKLIST.md`; release-doc tests; `tools/release_preflight.ps1 -RunSourceSmoke`; `tools/architect_signoff_check.ps1` with behavioral pass/fail fixture tests; `ARCHITECT_SIGNOFF.md` packet | Architect acceptance |

## Current Blocking Conditions
- Architect sign-off is still required for P0-A4 and P3-A4; use `ARCHITECT_SIGNOFF.md` and verify with `tools/architect_signoff_check.ps1`.
- Architect review is still required for decision-log items marked pending review; use `ARCHITECT_SIGNOFF.md` and verify with `tools/architect_signoff_check.ps1`.
- Upstream graph reconciliation is cleared in the `roadmap-integration` worktree; rerun `tools/upstream_reconciliation.ps1` and `tools/roadmap_audit.ps1` before release to confirm `behind=0`.
- Hosted macOS package build and non-audio smoke evidence exists, but visible menu-bar/tray and audible lifecycle evidence remain pending; final release should pass `tools/packaging_validation_check.ps1`.
- Hosted Windows package build and headless non-audio smoke evidence exists, but audible preview/speak/stop evidence remains pending; final release should pass `tools/packaging_validation_check.ps1`.
- Manual smoke tests remain for Tk desktop, Chrome extension popup, `/control` audio preview, packaged macOS lifecycle, and packaged Windows lifecycle. Use `tools/release_preflight.ps1 -RunSourceSmoke` first, `tools/server_smoke.ps1` for non-audio API/control checks, and `tools/manual_smoke_check.ps1` after filling interactive smoke evidence.

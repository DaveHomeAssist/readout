# ReadOut Milestone Log

## Status update - 2026-06-21 06:33 -04:00
- **Now:** Phase 0 Codex implementation complete for CORS/Origin hardening, config key redaction, and regression coverage.
- **Next:** Architect sign-off for P0-A4 local-only threat model.
- **Tests:** `python -m pytest` passed; live curl origin matrix passed against a temporary uvicorn server.
- **Blockers:** No Python 3.10-3.12 interpreter was available on this Windows host; verification ran on Python 3.13 with lightweight dev dependencies.
- **Decisions needed (Architect):** Confirm threat model assumptions and whether a shared-secret extension header is required in a later phase.

### P0-A1 - Completed
- **Done when:** CORS rejects unknown origins by default, and only explicit local allowlist origins are accepted.
- **What changed:** Replaced regex CORS middleware with a server-side Origin guard and explicit allowlist. Browser requests from untrusted origins now return `403` before endpoint code runs. Extension origins must be exact entries in `allowed_origins` or `READOUT_ALLOWED_ORIGINS`.
- **Tests run:**
  - `python -m pytest`
  - Temporary uvicorn server plus `curl.exe` origin matrix
- **Evidence:**

| Case | HTTP | Access-Control-Allow-Origin |
|---|---:|---|
| no-origin status | 200 | `<none>` |
| allowed local status | 200 | `http://localhost:7778` |
| allowed extension preflight | 204 | `chrome-extension://abcdefghijklmnopabcdefghijklmnop` |
| blocked evil status | 403 | `<none>` |
| blocked evil stop | 403 | `<none>` |

- **Notes / risks:** Local no-Origin callers remain allowed for desktop UI, curl, and scripts. Browser extension users must add their exact Chrome extension origin to config or env.
- **Follow-ups:** Architect should decide whether to add a shared-secret request header for stronger local API control.

### P0-A2 - Completed
- **Done when:** `/config` never returns provider keys in plaintext, even if set.
- **What changed:** Existing API-key redaction was preserved and extended around the new `allowed_origins` config path. Wildcard origins are discarded during normalization.
- **Tests run:** `python -m pytest`
- **Evidence:** Regression tests verify OpenAI and ElevenLabs keys are redacted from `/config` responses, plaintext secrets are absent from response text, and persisted keys remain available on disk for engine use.
- **Notes / risks:** `allowed_origins` is not secret and is intentionally returned as config.
- **Follow-ups:** None for Phase 0.

### P0-A3 - Completed
- **Done when:** Tests cover success and failure paths for `/config`, `/speak`, `/stop`, `/status`, and `/voices`.
- **What changed:** Added CORS/Origin regression cases across all five endpoints, status load-error coverage, and config allowlist normalization coverage.
- **Tests run:** `python -m pytest`
- **Evidence:** `62 passed, 1 warning in 1.74s`
- **Notes / risks:** Warning is from FastAPI/Starlette TestClient deprecation under the installed dependency set.
- **Follow-ups:** Re-run on Python 3.10-3.12 before packaging because Kokoro runtime excludes Python 3.13.

### P0-A4 - Pending Architect
- **Done when:** One-page threat model documents actors, assets, trust boundaries, and explicit local-only assumptions.
- **Notes / risks:** Codex implementation assumes local no-Origin callers are trusted enough for Phase 0 and blocks remote browser drive-by origins. Architect sign-off is still required.

## Status update - 2026-06-21 06:47 -04:00
- **Now:** Phase 1 UI truthfulness cleanup implemented.
- **Next:** Phase 2 control-surface polish, starting with extension popup status/error text.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** Formal Architect sign-off is still pending for P0-A4 and Phase 1 decisions, but the implementation decisions are logged in `DECISION_LOG.md`.
- **Decisions needed (Architect):** Confirm or revise P1-A2 Browser tab removal, P1-A4 Auto-read removal, and P1-A5 queue download button removal.

### P1-A1 - Completed
- **Done when:** UI label matches actual output, no other copy references MP3 unless supported.
- **What changed:** Desktop save button and built-in guide now say Save WAV. Usage docs were updated to match.
- **Tests run:** `python -m pytest`
- **Evidence:** Regression test verifies Save WAV copy and blocks Save MP3 user-facing copy from returning.
- **Notes / risks:** The only remaining MP3 reference is a technical server comment describing ElevenLabs' streamed input format.
- **Follow-ups:** None.

### P1-A2 - Completed, Pending Architect Review
- **Done when:** Decision: delete vs implement. If kept, it is functional and testable.
- **What changed:** Removed the nonfunctional Browser engine tab. Backend config now rejects unsupported `engine` values such as `browser`.
- **Tests run:** `python -m pytest`
- **Evidence:** UI regression test verifies supported engines are only `kokoro`, `openai`, and `elevenlabs`; API test verifies `PATCH /config` rejects `engine: browser`.
- **Notes / risks:** Decision rationale is recorded in `DECISION_LOG.md`.
- **Follow-ups:** Architect can revisit when a browser/system TTS backend has a concrete implementation plan.

### P1-A3 - Completed
- **Done when:** Desktop toggles mutate backend config and persist across restart.
- **What changed:** Desktop engine tabs now PATCH `/config`; voice and speed controls also persist to config; status polling applies persisted engine/voice/speed to the desktop UI on startup.
- **Tests run:** `python -m pytest`
- **Evidence:** UI helper tests verify PATCH request formation and config ID-to-label voice mapping.
- **Notes / risks:** Desktop UI smoke was not launched because this environment is not set up for interactive Tk window verification.
- **Follow-ups:** Run a manual desktop smoke test on the target workstation before release packaging.

### P1-A4 - Completed, Pending Architect Review
- **Done when:** Decision logged. If implemented, includes safe defaults and clear UI state.
- **What changed:** Removed the nonfunctional Auto-read button.
- **Tests run:** `python -m pytest`
- **Evidence:** UI regression test verifies no visible Auto-read control remains in `ui.py`.
- **Notes / risks:** Decision rationale is recorded in `DECISION_LOG.md`.
- **Follow-ups:** Reintroduce only after trigger behavior and safe defaults are specified.

### P1-A5 - Completed, Pending Architect Review
- **Done when:** Decision logged. If implemented, downloads are correct format and named deterministically.
- **What changed:** Removed queue-row download buttons with no command handler.
- **Tests run:** `python -m pytest`
- **Evidence:** UI regression test verifies the inert queue download button block is gone.
- **Notes / risks:** Decision rationale is recorded in `DECISION_LOG.md`.
- **Follow-ups:** Reintroduce after queue items track saved WAV paths or deterministic regeneration inputs.

## Status update - 2026-06-21 06:49 -04:00
- **Now:** P2-A2 extension popup status/error text implemented.
- **Next:** P2-A3 voice preview snippets.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** No browser-extension runtime smoke test was run in Chrome.
- **Decisions needed (Architect):** P2-A4 history retention and privacy model remains pending.

### P2-A2 - Completed
- **Done when:** Extension displays server up/down, last error, and next action clearly.
- **What changed:** Added a popup status-detail region and explicit messages for connected, loading, model-error, offline, no-selection, speak failure, stop failure, and config-save failure paths.
- **Tests run:** `python -m pytest`
- **Evidence:** Popup regression tests verify the detail region and required next-action/error strings. Full suite output: `70 passed, 1 warning in 1.28s`.
- **Notes / risks:** Source-level regression coverage only; Chrome popup was not manually opened in this environment.
- **Follow-ups:** Manual extension smoke test in Chrome before release.

## Status update - 2026-06-21 06:53 -04:00
- **Now:** P2-A3 voice preview snippets implemented.
- **Next:** P3-A3 first-run dependency checks or P3 packaging validation, depending on target platform priority.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** P2-A1 and P2-A4 remain Architect-owned decisions.
- **Decisions needed (Architect):** Confirm `/control` as official macOS primary UI and define history retention/privacy policy.

### P2-A3 - Completed
- **Done when:** Users can play short previews per voice without configuring a full read.
- **What changed:** Added `POST /preview` with a fixed short sample phrase, request-local engine/voice/speed selection, and save suppression even when `always_save` is enabled. Added Preview controls to `/control`, desktop UI, and extension popup.
- **Tests run:** `python -m pytest`
- **Evidence:** API tests verify preview text, no config mutation, engine override behavior, unsupported-engine rejection, and no save despite `always_save`. UI/popup tests verify Preview controls and `/preview` request wiring. Full suite output: `77 passed, 1 warning in 1.57s`.
- **Notes / risks:** Source-level UI coverage only; audio playback was not manually verified in Tk, Chrome, or the browser control panel in this environment.
- **Follow-ups:** Manual voice-preview smoke test on the target machine before release.

## Status update - 2026-06-21 06:57 -04:00
- **Now:** P3-A3 first-run dependency checks implemented.
- **Next:** P3-A2 Windows build validation is the next Codex-owned item feasible on this machine, but it requires a supported Python 3.10-3.12 runtime and full runtime dependencies.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** Current `python` is 3.13, which the new checker correctly reports as unsupported for Kokoro.
- **Decisions needed (Architect):** P3-A4 release checklist remains Architect-owned.

### P3-A3 - Completed
- **Done when:** Python/Kokoro/espeak-ng missing state is detected and explained.
- **What changed:** Added lightweight dependency checks for Python 3.10-3.12, the `kokoro` package, and `espeak-ng` on PATH. Startup prints actionable dependency reports, `/status` exposes `dependency_issues`, popup/control panel display dependency messages, and Windows build preflight rejects unsupported Python.
- **Tests run:** `python -m pytest`
- **Evidence:** Dependency tests cover pass/fail states and formatted reports; status tests verify machine-readable dependency issues; startup test verifies dependency reporting before tray imports. Full suite output: `82 passed, 1 warning in 1.77s`.
- **Notes / risks:** Runtime dependency checks were unit-tested with injected finders; no full packaged first-run smoke was performed.
- **Follow-ups:** Re-run startup on a clean Python 3.10-3.12 environment with and without `espeak-ng` installed.

## Status update - 2026-06-21 07:02 -04:00
- **Now:** P2-A1 and P2-A4 implemented with decision-log entries.
- **Next:** Packaging validation remains, but macOS requires a macOS target and Windows requires Python 3.10-3.12 plus runtime dependencies.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** This host only reports Python 3.13 and no `espeak-ng` on PATH, so a production Windows build cannot be validated here yet.
- **Decisions needed (Architect):** P0-A4 threat model sign-off and P3-A4 release checklist remain.

### P2-A1 - Completed, Pending Architect Review
- **Done when:** Docs and UI agree. Primary workflows are reachable from `/control`.
- **What changed:** macOS now routes to the browser control panel by default unless `READOUT_FORCE_TK=1` is set. `/control` copy describes itself as the primary macOS control surface, and docs match that flow.
- **Tests run:** `python -m pytest`
- **Evidence:** Runtime tests verify macOS uses `/control` by default, force-Tk override still works, and non-macOS uses Tk by default. Control-panel tests verify primary macOS copy and core controls are present.
- **Notes / risks:** Runtime browser launch was not manually smoke-tested on macOS in this environment.
- **Follow-ups:** Manual tray-to-control-panel smoke test on macOS before release.

### P2-A4 - Completed, Pending Architect Review
- **Done when:** Decision on retention and storage. UI shows clear on/off and delete history.
- **What changed:** Added local-only recent-read history that is off by default, capped by `history_limit`, stored in `~/.readout/history.json`, and clearable from `/control` or `DELETE /history`.
- **Tests run:** `python -m pytest`
- **Evidence:** History tests verify disabled default, enabled storage, limit capping, clear behavior, API responses, and control-panel privacy controls. Full suite output: `93 passed, 1 warning in 2.11s`.
- **Notes / risks:** History stores read text locally in plaintext when enabled. This is intentional and documented; default is off.
- **Follow-ups:** Architect should confirm this retention/privacy model before release.

## Status update - 2026-06-21 07:05 -04:00
- **Now:** P0-A4 threat model draft and P3-A4 release checklist are documented.
- **Next:** Packaging validation remains split by platform: macOS requires a macOS target, and Windows requires Python 3.10-3.12 plus runtime dependencies.
- **Tests:** `python -m pytest` passed; `git diff --check` passed.
- **Blockers:** Current Windows host has Python 3.13 and no `espeak-ng` on PATH, so production packaging cannot be validated here yet.
- **Decisions needed (Architect):** Threat model sign-off, release checklist acceptance, and the decision-log items marked pending review.

### P0-A4 - Drafted, Pending Architect Sign-off
- **Done when:** One-page threat model complete and signed off.
- **What changed:** Added `THREAT_MODEL.md` covering assets, trust boundaries, controls, residual risks, and sign-off status.
- **Tests run:** `python -m pytest`
- **Evidence:** Full suite output after adding documentation checks: `95 passed, 1 warning in 1.93s`.
- **Notes / risks:** The document is drafted, but formal Architect sign-off is still pending.
- **Follow-ups:** Architect should review and sign off before release.

### P3-A4 - Drafted, Pending Architect Acceptance
- **Done when:** Release checklist agreed.
- **What changed:** Added `RELEASE_CHECKLIST.md` with security, test, macOS build, Windows build, release notes, rollback, and sign-off gates.
- **Tests run:** `python -m pytest`
- **Evidence:** Release-doc regression tests verify the checklist includes the required release-gate sections.
- **Notes / risks:** Checklist acceptance is still pending.
- **Follow-ups:** Architect should confirm release criteria before packaging.

## Status update - 2026-06-21 07:09 -04:00
- **Now:** P3 packaging scripts fail earlier and more clearly when prerequisites are missing.
- **Next:** Full P3-A1/P3-A2 packaging validation still requires target environments with supported runtimes.
- **Tests:** `python -m pytest` passed with `97 passed, 1 warning in 2.24s`.
- **Blockers:** This Windows host has only Python 3.13 registered through the Python launcher, the `python` shim is broken in the sandbox, `espeak-ng` is missing, and no bash/macOS environment is available for `build_mac.sh` syntax or app validation.
- **Decisions needed (Architect):** Release checklist acceptance and remaining pending decision-log sign-offs.

### P3-A1 - Preflight Hardened, Validation Pending macOS
- **Done when:** Build produces runnable app, tray + control panel lifecycle verified.
- **What changed:** `build_mac.sh` now validates Python 3.10-3.12 even for an existing `.venv`, checks `espeak-ng` before dependency install, and runs PyInstaller through `.venv/bin/python -m PyInstaller`.
- **Tests run:** `python -m pytest`
- **Evidence:** Build-script regression tests verify the macOS script has supported-Python selection, `.venv` revalidation, `espeak-ng` preflight, and module-based PyInstaller invocation.
- **Notes / risks:** Full app build and tray/control-panel lifecycle validation still require a macOS target.
- **Follow-ups:** Run `./build_mac.sh`, launch `dist/ReadOut.app`, and record tray/control-panel lifecycle results on macOS.

### P3-A2 - Preflight Hardened, Validation Pending Windows Runtime
- **Done when:** Build produces runnable app, server lifecycle verified on Windows.
- **What changed:** `build_windows.ps1` now avoids trusting the WindowsApps `python` shim, prefers `py -3.12`, `py -3.11`, `py -3.10`, validates existing `.venv`, checks `espeak-ng` before dependency install, and runs PyInstaller through the venv Python module.
- **Tests run:** `python -m pytest`; `.\build_windows.ps1`
- **Evidence:** Local build preflight stopped before install/build with `ERROR: Python 3.10-3.12 is required for Kokoro.` Focused tests passed, and full suite output was `97 passed, 1 warning in 2.24s`.
- **Notes / risks:** No `ReadOut.exe` was built because this host lacks a supported Python 3.10-3.12 runtime and `espeak-ng`.
- **Follow-ups:** Install Python 3.10-3.12 and `espeak-ng`, then run `.\build_windows.ps1` and record server lifecycle smoke results.

## Status update - 2026-06-21 07:12 -04:00
- **Now:** Repeatable Phase 0 live CORS matrix helper and stronger P1-A3 persistence tests are in place.
- **Next:** Remaining completion items are still target-environment packaging validation and Architect sign-offs.
- **Tests:** `python -m pytest` passed with `100 passed, 1 warning in 1.74s`.
- **Blockers:** Live CORS matrix was not run because the server was not started in this sandbox pass; macOS and Windows packaging validation still require target prerequisites.
- **Decisions needed (Architect):** Threat model sign-off, release checklist acceptance, and pending decision-log reviews.

### P0-A1 - Evidence Strengthened
- **Done when:** CORS rejects unknown origins by default, and only explicit local allowlist origins are accepted.
- **What changed:** Added `tools/cors_origin_matrix.ps1` so the live curl proof matrix can be rerun against a running ReadOut instance instead of relying on a one-off transcript.
- **Tests run:** `python -m pytest`; PowerShell parser check for `tools/cors_origin_matrix.ps1`.
- **Evidence:** Script covers no-origin status, allowed local status, allowed local config preflight, blocked evil status, blocked evil stop, and optional allowlisted extension preflight. Static helper test and parser check passed.
- **Notes / risks:** Run the script only after starting ReadOut; it exits nonzero if any matrix row fails.
- **Follow-ups:** Run `.\tools\cors_origin_matrix.ps1` during the release security gate and paste the table into this log.

### P1-A3 - Evidence Strengthened
- **Done when:** Desktop toggles mutate backend config and persist across restart.
- **What changed:** Added method-level desktop UI tests that prove engine, voice, and speed controls PATCH persistable config payloads, and status polling applies persisted engine/voice/speed without writing back.
- **Tests run:** `python -m pytest`
- **Evidence:** Focused UI/CORS helper tests passed with `9 passed in 0.12s`; full suite passed with `100 passed, 1 warning in 1.74s`.
- **Notes / risks:** Interactive Tk smoke is still a release-checklist item, but the persistence contract is now covered without launching a desktop window.
- **Follow-ups:** Run desktop UI smoke on a target workstation before packaging release.

## Status update - 2026-06-21 07:13 -04:00
- **Now:** Roadmap readiness is summarized in a dedicated status artifact.
- **Next:** Use `ROADMAP_STATUS.md` as the short audit view while `MILESTONE_LOG.md` remains the evidence log.
- **Tests:** `python -m pytest` passed with `102 passed, 1 warning in 1.71s`.
- **Blockers:** No `.venv` exists in this repo, and target packaging validation still requires supported runtimes plus macOS/Windows smoke environments.
- **Decisions needed (Architect):** Threat model sign-off, release checklist acceptance, and pending decision-log reviews.

### Roadmap Audit Artifact - Added
- **Done when:** Every roadmap item has a visible status, evidence pointer, and remaining proof item.
- **What changed:** Added `ROADMAP_STATUS.md` with a phase-by-phase table for P0-A1 through P3-A4 and current blocking conditions.
- **Tests run:** `python -m pytest tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Release-doc tests verify all roadmap item rows are present and README links the release-readiness artifacts. Focused docs output: `4 passed in 0.12s`; full suite output: `102 passed, 1 warning in 1.71s`.
- **Notes / risks:** The artifact intentionally marks Architect sign-offs and target packaging validation as not complete.
- **Follow-ups:** Update `ROADMAP_STATUS.md` after Architect decisions and after macOS/Windows packaging smoke tests.

## Status update - 2026-06-21 07:20 -04:00
- **Now:** Non-audio API/control smoke testing is repeatable from PowerShell.
- **Next:** Run `tools/server_smoke.ps1` against a live source or packaged server, then use manual checks only for audio, browser-extension, and tray lifecycle behavior.
- **Tests:** `python -m pytest` passed with `103 passed, 1 warning in 2.34s`.
- **Blockers:** The helper was parsed and tested, but not run against a live server in this pass because no `.venv` or release runtime is present.
- **Decisions needed (Architect):** Threat model sign-off, release checklist acceptance, and pending decision-log reviews.

### Release Smoke Helper - Added
- **Done when:** Non-audio API/control checks can be repeated without mutating config or playing audio.
- **What changed:** Added `tools/server_smoke.ps1` for `/status`, `/voices`, `/history`, and `/control` checks. `/preview` is guarded behind `-IncludeAudio`.
- **Tests run:** PowerShell parser check; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Both PowerShell release helpers parse cleanly. Focused release-tool/doc tests passed with `6 passed in 0.08s`; full suite passed with `103 passed, 1 warning in 2.34s`.
- **Notes / risks:** This does not replace manual audio preview, Chrome extension popup, or packaged tray lifecycle smoke tests.
- **Follow-ups:** After starting ReadOut, run `.\tools\server_smoke.ps1`; use `.\tools\server_smoke.ps1 -IncludeAudio` only when intentionally testing voice preview playback.

## Status update - 2026-06-21 07:23 -04:00
- **Now:** Release readiness can be checked with a single local preflight command.
- **Next:** On a target release machine, run `.\tools\release_preflight.ps1 -RunPytest -RunLiveChecks` after starting ReadOut.
- **Tests:** `python -m pytest` passed with `104 passed, 1 warning in 1.95s`.
- **Blockers:** Local preflight correctly fails this host for missing Python 3.10-3.12 and missing `espeak-ng`.
- **Decisions needed (Architect):** Threat model sign-off, release checklist acceptance, and pending decision-log reviews.

### Release Preflight Helper - Added
- **Done when:** Required artifacts, PowerShell syntax, Python runtime, `espeak-ng`, optional pytest, and optional live server checks can be summarized from one command.
- **What changed:** Added `tools/release_preflight.ps1` and linked it from README and `RELEASE_CHECKLIST.md`.
- **Tests run:** PowerShell parser check; `.\tools\release_preflight.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Preflight passed required artifact and script syntax checks, then failed the local host with explicit Python 3.10-3.12 and `espeak-ng` messages. Focused release tests passed with `7 passed in 0.12s`; full suite passed with `104 passed, 1 warning in 1.95s`.
- **Notes / risks:** The preflight is a gate, not a build. It intentionally exits nonzero when packaging prerequisites are missing.
- **Follow-ups:** Re-run preflight after installing Python 3.10-3.12 and `espeak-ng`; add `-RunPytest -RunLiveChecks` on the release target.

## Status update - 2026-06-21 07:26 -04:00
- **Now:** Pending Architect decisions are consolidated into one sign-off packet.
- **Next:** Architect can review `ARCHITECT_SIGNOFF.md`, mark accept/revise, then copy final decisions into `DECISION_LOG.md`.
- **Tests:** `python -m pytest` passed with `105 passed, 1 warning in 2.13s`.
- **Blockers:** Sign-off itself remains external; local preflight still fails this host for missing Python 3.10-3.12 and missing `espeak-ng`.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Architect Sign-off Packet - Added
- **Done when:** Every Architect-owned pending decision has a visible accept/revise row and evidence pointers.
- **What changed:** Added `ARCHITECT_SIGNOFF.md`, linked it from README and the release checklist, included it in `ROADMAP_STATUS.md`, and made `tools/release_preflight.ps1` require it as a release artifact.
- **Tests run:** PowerShell parser check; `.\tools\release_preflight.ps1`; `python -m pytest tests/test_release_docs.py tests/test_release_tools.py`; `python -m pytest`
- **Evidence:** Preflight now verifies `ARCHITECT_SIGNOFF.md` is present before reporting the known runtime prerequisite failures. Focused release docs/tool tests passed with `8 passed in 0.28s`; full suite passed with `105 passed, 1 warning in 2.13s`.
- **Notes / risks:** The packet does not approve anything by itself. It only makes the external review explicit and repeatable.
- **Follow-ups:** Architect should mark each row Accept or Revise, then update `DECISION_LOG.md` and `ROADMAP_STATUS.md`.

## Status update - 2026-06-21 07:30 -04:00
- **Now:** Windows packaged lifecycle validation has a repeatable helper.
- **Next:** After `.\build_windows.ps1` succeeds on a supported runtime, run `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe`.
- **Tests:** `python -m pytest` passed with `106 passed, 1 warning in 2.25s`.
- **Blockers:** No packaged exe exists on this host because Python 3.10-3.12 and `espeak-ng` are missing.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### P3-A2 - Windows Package Smoke Helper Added
- **Done when:** Build produces runnable app, server lifecycle verified on Windows.
- **What changed:** Added `tools/windows_package_smoke.ps1` to launch `dist\ReadOut\ReadOut.exe`, wait for `/status`, run the non-audio server smoke and CORS matrix helpers, then stop the launched process.
- **Tests run:** PowerShell parser check; `.\tools\windows_package_smoke.ps1`; `.\tools\release_preflight.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** The helper parses cleanly and fails clearly when `dist\ReadOut\ReadOut.exe` is missing. Preflight now requires the helper artifact. Focused release tests passed with `9 passed in 0.13s`; full suite passed with `106 passed, 1 warning in 2.25s`.
- **Notes / risks:** This still does not validate P3-A2 on this host because no supported Python/runtime build exists yet.
- **Follow-ups:** Install Python 3.10-3.12 and `espeak-ng`, build with `.\build_windows.ps1`, then run the package smoke helper and paste the result here.

## Status update - 2026-06-21 07:34 -04:00
- **Now:** macOS packaged lifecycle validation has a repeatable helper.
- **Next:** After `./build_mac.sh` succeeds on macOS, run `./tools/mac_package_smoke.sh --app dist/ReadOut.app`, then manually verify the menu-bar tray icon.
- **Tests:** `python -m pytest` passed with `107 passed, 1 warning in 2.22s`.
- **Blockers:** This Windows host has no bash/macOS target, so the shell helper is statically covered but not target-executed here.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### P3-A1 - macOS Package Smoke Helper Added
- **Done when:** Build produces runnable app, tray + control panel lifecycle verified.
- **What changed:** Added `tools/mac_package_smoke.sh` to launch `dist/ReadOut.app`, wait for `/status`, verify `/voices`, `/history`, `/control`, optionally run `/preview`, check blocked-origin behavior, and quit ReadOut.
- **Tests run:** PowerShell preflight artifact check; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Preflight now requires `tools/mac_package_smoke.sh`; focused release tests passed with `10 passed in 0.07s`; full suite passed with `107 passed, 1 warning in 2.22s`.
- **Notes / risks:** Bash/macOS execution was not run on this Windows host. Manual tray icon verification still remains because the helper validates server/control lifecycle, not menu-bar rendering.
- **Follow-ups:** On macOS, run `chmod +x tools/mac_package_smoke.sh` if needed, then `./tools/mac_package_smoke.sh --app dist/ReadOut.app` and record output here.

## Status update - 2026-06-21 07:38 -04:00
- **Now:** Target packaging evidence has a dedicated worksheet.
- **Next:** Fill `PACKAGING_VALIDATION.md` on macOS and Windows targets, then paste completed tables into this log.
- **Tests:** `python -m pytest` passed with `108 passed, 1 warning in 3.82s`.
- **Blockers:** The worksheet is ready, but actual P3-A1/P3-A2 validation still needs target builds.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Packaging Validation Worksheet - Added
- **Done when:** Target build/smoke evidence for P3-A1 and P3-A2 can be captured consistently.
- **What changed:** Added `PACKAGING_VALIDATION.md` with macOS and Windows command blocks, result tables, release evidence summary, and accepted-gap table. Linked it from README, `RELEASE_CHECKLIST.md`, `ROADMAP_STATUS.md`, and `tools/release_preflight.ps1`.
- **Tests run:** PowerShell parser check; `.\tools\release_preflight.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Preflight now requires `PACKAGING_VALIDATION.md`. Focused release tests passed with `11 passed in 0.19s`; full suite passed with `108 passed, 1 warning in 3.82s`.
- **Notes / risks:** This does not itself validate packaged apps. It standardizes the target evidence that still needs to be produced.
- **Follow-ups:** Complete the worksheet on macOS/Windows packaging targets and update `ROADMAP_STATUS.md` after successful runs.

## Status update - 2026-06-21 07:43 -04:00
- **Now:** Release secret scanning is repeatable and part of preflight.
- **Next:** Keep using `.\tools\secret_scan.ps1` before release and let `.\tools\release_preflight.ps1` run it automatically.
- **Tests:** `python -m pytest` passed with `109 passed, 1 warning in 3.48s`.
- **Blockers:** Packaging/sign-off blockers remain unchanged.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Release Secret Scan - Added
- **Done when:** Release gate can verify common provider key literals and committed non-empty provider keys are not present.
- **What changed:** Added `tools/secret_scan.ps1`, linked it from README and `RELEASE_CHECKLIST.md`, and made `tools/release_preflight.ps1` run it in quiet mode.
- **Tests run:** PowerShell parser check; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`
- **Evidence:** Secret scan passed with `No provider key literals found`. Preflight reports `Secret scan | PASS | secret_scan.ps1 exit=0`. Focused release tests passed with `12 passed in 1.17s`; full suite passed with `109 passed, 1 warning in 3.48s`.
- **Notes / risks:** The scan is a release safety net, not a substitute for code review or checking local untracked config outside the repo.
- **Follow-ups:** Keep provider keys in `~/.readout/config.json` or environment-specific storage, never in committed files.

## Status update - 2026-06-21 07:47 -04:00
- **Now:** Current-state audit confirms the remaining roadmap gaps are external sign-off and target-machine validation, not known local code/test gaps.
- **Next:** Architect should complete `ARCHITECT_SIGNOFF.md`; packaging owner should run `PACKAGING_VALIDATION.md` on macOS and Windows targets.
- **Tests:** `python -m pytest` passed with `109 passed, 1 warning in 2.85s`.
- **Blockers:** `.\tools\release_preflight.ps1` still correctly fails this host for missing Python 3.10-3.12 and missing `espeak-ng`; `.\tools\windows_package_smoke.ps1` correctly fails because `dist\ReadOut\ReadOut.exe` does not exist.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Current Roadmap Completion Audit - Refreshed
- **Done when:** The active roadmap has current evidence for all local implementation/test items and explicit blockers for owner/target-machine items.
- **What changed:** Refreshed `ROADMAP_STATUS.md` timestamp and recorded the latest audit evidence here.
- **Tests run:** `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`; `.\tools\windows_package_smoke.ps1`
- **Evidence:** Full suite passed with `109 passed, 1 warning in 2.85s`. Secret scan passed with `No provider key literals found`. Preflight passed required file checks, PowerShell syntax checks, and secret scan, then failed the expected local prerequisites: Python 3.10-3.12 and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings. Windows package smoke reported `Executable not found: dist\ReadOut\ReadOut.exe`.
- **Notes / risks:** Live source-server smoke, Chrome extension runtime smoke, audio preview, macOS packaged lifecycle, Windows packaged lifecycle, and tray/menu-bar visual verification remain unproven in this environment.
- **Follow-ups:** Run `.\tools\release_preflight.ps1 -RunPytest -RunLiveChecks` on a supported Windows runtime after starting ReadOut; run `./build_mac.sh` and `./tools/mac_package_smoke.sh --app dist/ReadOut.app` on macOS; fill `PACKAGING_VALIDATION.md` with actual target results.

## Status update - 2026-06-23 06:08 -04:00
- **Now:** Roadmap status reflects that local `main` is behind `origin/main` by 10 relevant ReadOut commits.
- **Next:** Reconcile upstream architecture changes with this roadmap branch before claiming release readiness.
- **Tests:** `python -m pytest` passed with `109 passed, 1 warning in 6.19s`.
- **Blockers:** Upstream reconciliation is now a tracked blocker in addition to Architect sign-off and target packaging validation. This host still has only Python 3.13 via the launcher, no `.venv`, no `espeak-ng`, and no packaged `dist\ReadOut\ReadOut.exe`.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Upstream Divergence Audit - Added
- **Done when:** Release-readiness docs prevent stale-branch release claims and identify upstream changes that must be reconciled safely.
- **What changed:** Added an upstream integration risk to `ROADMAP_STATUS.md`, added the same blocker to `ARCHITECT_SIGNOFF.md`, and added a release-checklist precondition to confirm the branch is up to date with `origin/main` or the remote delta has been reviewed and accepted.
- **Tests run:** `git log --oneline --decorate --left-right HEAD...origin/main`; `git show origin/main:tests/test_server_cors.py`; `py -0p`; `Get-Command espeak-ng`; `python -m pytest`; `.\tools\release_preflight.ps1`; `.\tools\secret_scan.ps1`; `git diff --check`
- **Evidence:** `origin/main` is 10 commits ahead, including engine registry, unified voice catalogue, web-control-panel redesign, Tk retirement, startup-race hardening, and feature-spec commits. Remote CORS tests allow arbitrary `chrome-extension://...` origins, while this roadmap branch requires explicit trusted origins. Full suite passed with `109 passed, 1 warning in 6.19s`. Secret scan passed. Preflight passed required artifact, syntax, and secret checks, then failed the expected local prerequisites: Python 3.10-3.12 and `espeak-ng`.
- **Notes / risks:** Do not run a blind `git pull` into this dirty worktree. Reconcile upstream in a reviewable branch/worktree so exact-origin CORS, preview, history, dependency checks, release preflight, sign-off packet, and packaging validation are preserved.
- **Follow-ups:** Build an integration branch from `origin/main`, port the roadmap artifacts/features onto it, rerun the full suite and release preflight, then update this log with the resolved diff.

## Status update - 2026-06-23 06:16 -04:00
- **Now:** Safe upstream engine/security pieces are ported into the roadmap worktree without replacing the exact-origin CORS guard or dropping preview/history/release-gate work.
- **Next:** Review the remaining upstream UI/spec/packaging deltas, especially web-control-panel redesign, Tk retirement, `FEATURE-SPEC.md`, and spec/build differences.
- **Tests:** `python -m pytest` passed with `120 passed, 1 warning in 2.04s`.
- **Blockers:** The branch is still behind `origin/main` at the Git graph level; this host still lacks Python 3.10-3.12, `.venv`, `espeak-ng`, and packaged app outputs.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Upstream Engine/Security Reconciliation - Partial
- **Done when:** Useful upstream changes are integrated without weakening roadmap security/privacy/release requirements.
- **What changed:** Added `engines/` registry package; routed OpenAI and ElevenLabs synthesis through registry adapters; exposed per-engine capability/voice metadata from `/voices`; made `/control` and extension popup consume the registry catalogue with static fallbacks; added startup wait before model warmup; disabled FastAPI docs/OpenAPI; added loopback Host guard; removed unused extension `storage` permission; bumped extension manifest to 1.3; hardened config file and directory permissions.
- **Tests run:** `python -m pytest tests/test_engines.py tests/test_server_api.py tests/test_server_cors.py tests/test_extension_popup.py tests/test_main_runtime.py tests/test_engine_fallbacks.py`; `python -m pytest tests/test_release_docs.py tests/test_release_tools.py tests/test_build_scripts.py tests/test_ui_copy.py tests/test_config.py tests/test_dependency_check.py tests/test_history_store.py tests/test_tts_engine.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** Focused runtime/security suite passed with `73 passed, 1 warning in 1.89s`. Remaining focused checks passed with `47 passed in 0.59s`. Full suite passed with `120 passed, 1 warning in 2.04s`. Secret scan passed. Preflight passed required artifact, syntax, and secret checks, then failed only the expected local prerequisites: Python 3.10-3.12 and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This is a selective port, not a merge. `origin/main` still has remaining relevant commits and Git still reports this branch as behind 10.
- **Follow-ups:** Continue reconciling upstream in small reviewable cuts, then run release preflight with `-RunPytest -RunLiveChecks` on a supported target runtime.

### Release Preflight - Upstream Currency Gate Added
- **Done when:** Release preflight catches a stale branch before package validation or release sign-off.
- **What changed:** `tools/release_preflight.ps1` now compares `HEAD...@{u}` and fails when the current branch is behind upstream. `tests/test_release_tools.py` locks in this check.
- **Tests run:** `python -m pytest tests/test_release_docs.py tests/test_release_tools.py`; `.\tools\release_preflight.ps1`
- **Evidence:** Focused release docs/tools tests passed with `12 passed in 0.13s`. Preflight now reports `Git upstream currency | FAIL | Branch is behind origin/main by 10 commit(s); ahead by 0.` before the known Python 3.10-3.12 and `espeak-ng` prerequisite failures.
- **Notes / risks:** The check is local-only and does not fetch. Run `git fetch` separately before final release preflight if remote freshness matters.

### Feature Spec / Packaging Hidden Imports - Added
- **Done when:** Current behavior and release blockers are documented, and packaged builds explicitly include the pluggable engine modules.
- **What changed:** Added `FEATURE-SPEC.md`, linked it from README release gates, and added `engines.*` hidden imports to `ReadOut.spec`.
- **Tests run:** `python -m pytest tests/test_release_docs.py tests/test_build_scripts.py tests/test_release_tools.py`
- **Evidence:** Focused release docs/build/tool checks passed with `16 passed in 0.12s`.
- **Notes / risks:** This is an as-built spec for the roadmap branch, not Architect sign-off.

## Status update - 2026-06-23 06:19 -04:00
- **Now:** Final local verification after selective upstream reconciliation is green for tests and secret scan.
- **Next:** Remaining work is upstream graph reconciliation, Architect sign-off, and target-machine packaging validation.
- **Tests:** `python -m pytest` passed with `122 passed, 1 warning in 2.68s`.
- **Blockers:** `tools/release_preflight.ps1` now intentionally fails this host for Git upstream currency, Python 3.10-3.12, and `espeak-ng`.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

## Status update - 2026-06-23 06:24 -04:00
- **Now:** Tk desktop UI also consumes the unified `/voices` catalogue, so all active control surfaces share the registry-backed voice source.
- **Next:** Continue upstream reconciliation for remaining UI/spec/packaging deltas.
- **Tests:** `python -m pytest` passed with `124 passed, 1 warning in 2.46s`.
- **Blockers:** Release preflight still intentionally fails until upstream graph currency, Python 3.10-3.12, and `espeak-ng` are resolved.

### Desktop Voice Catalogue Alignment - Added
- **Done when:** Desktop controls no longer depend only on hardcoded voice lists when the server catalogue is available.
- **What changed:** `ui.py` now loads `/voices` once during status polling, converts engine voice metadata into display labels that preserve raw IDs for config patches, and keeps static fallback lists for offline/startup cases. `FEATURE-SPEC.md` records the shared catalogue behavior. `tools/release_preflight.ps1` now requires `FEATURE-SPEC.md`.
- **Tests run:** `python -m pytest tests/test_ui_copy.py tests/test_server_api.py tests/test_engines.py tests/test_extension_popup.py`
- **Evidence:** Focused suite passed with `44 passed, 1 warning in 1.31s`. Release docs/tool/UI checks passed with `23 passed in 0.21s`. Full suite passed with `124 passed, 1 warning in 2.46s`. Secret scan passed. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.

## Status update - 2026-06-23 06:31 -04:00
- **Now:** Source live HTTP smoke is covered by pytest, avoiding the broken Windows Python shim while still exercising real uvicorn loopback behavior.
- **Next:** Use this smoke test as the source-server gate; packaged lifecycle smoke still requires built app outputs.
- **Blockers:** Release preflight still intentionally fails until upstream graph currency, Python 3.10-3.12, and `espeak-ng` are resolved.

### Source Live HTTP Smoke - Added
- **Done when:** Core source-server HTTP routes and origin rejection are smoke-tested against a live loopback uvicorn server.
- **What changed:** Added `tests/test_live_http_smoke.py` to start uvicorn in-process on a temporary port, verify `/status`, `/voices`, `/history`, `/control`, dependency issue shape, and disallowed-origin rejection before `/speak` side effects. Added the smoke test to `RELEASE_CHECKLIST.md`.
- **Tests run:** `python -m pytest tests/test_live_http_smoke.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** Focused live-smoke/docs checks passed with `10 passed in 2.84s`. Full suite passed with `127 passed, 1 warning in 3.98s`. Secret scan passed. Preflight passed required artifact, PowerShell syntax, and secret checks, then intentionally failed Git upstream currency, Python 3.10-3.12, and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This is source-server validation, not packaged app lifecycle validation.

### Source Live HTTP Smoke - Expanded
- **Done when:** Live source-server checks cover the roadmap's highest-risk HTTP contracts, not only basic availability.
- **What changed:** Expanded `tests/test_live_http_smoke.py` with a live CORS origin matrix, live `/config` API-key redaction and history-control checks, and live `/preview` request-local behavior that proves preview does not save, mutate config, or add recent-read history.
- **Tests run:** `python -m pytest tests/test_live_http_smoke.py`; `python -m pytest tests/test_live_http_smoke.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** Expanded live smoke passed with `6 passed in 3.25s`. Focused live-smoke/docs checks passed with `13 passed in 3.33s`. Full suite passed with `131 passed, 1 warning in 5.09s`. Secret scan passed. Preflight passed required artifact, PowerShell syntax, and secret checks, then intentionally failed Git upstream currency, Python 3.10-3.12, and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** Still source-server only; packaged app lifecycle remains target-machine work.

## Status update - 2026-06-23 06:36 -04:00
- **Now:** macOS packaged entrypoint behavior has source-level regression coverage.
- **Next:** Actual P3-A1 still requires a macOS PyInstaller build and packaged app smoke.
- **Blockers:** macOS packaged lifecycle cannot be proven on this Windows host.

### macOS Packaged Entrypoint Coverage - Added
- **Done when:** The packaged macOS entrypoint is covered for tray/control-panel routing before target packaging.
- **What changed:** Added tests proving `main_app.main()` sets `READOUT_DISABLE_UI=1`, sets `READOUT_AUTO_OPEN_CONTROL=0`, and calls the normal app entrypoint with an empty argv. Added PyInstaller spec assertions that macOS packages use `main_app.py` and exclude Tk on Darwin.
- **Tests run:** `python -m pytest tests/test_main_runtime.py tests/test_build_scripts.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** Focused runtime/build tests passed with `8 passed in 0.13s`. Full suite passed with `128 passed, 1 warning in 3.70s`. Secret scan passed. Preflight passed required artifact, PowerShell syntax, and secret checks, then intentionally failed Git upstream currency, Python 3.10-3.12, and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This does not replace macOS target validation; it protects the source contract that the target build uses.

## Status update - 2026-06-23 06:31 -04:00
- **Now:** Release preflight can run the source live HTTP smoke gate directly.
- **Next:** Use `.\tools\release_preflight.ps1 -RunSourceSmoke` on a supported release runtime before packaged app validation.
- **Blockers:** This host still lacks the supported Python/espeak target prerequisites needed for release preflight to run optional Python-backed gates inside the script.

### Source Smoke Preflight Gate - Added
- **Done when:** The release preflight can explicitly run the in-process source-server smoke test without requiring a manually launched ReadOut server.
- **What changed:** Added `-RunSourceSmoke` to `tools/release_preflight.ps1`, wired it to `python -m pytest tests/test_live_http_smoke.py`, and linked the command from `README.md`, `RELEASE_CHECKLIST.md`, and `ROADMAP_STATUS.md`.
- **Tests run:** PowerShell parser check for `tools/release_preflight.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest tests/test_live_http_smoke.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1 -RunSourceSmoke`; `git diff --check`
- **Evidence:** Focused release docs/tools checks passed with `13 passed in 0.14s`. Source live HTTP smoke passed with `6 passed in 3.35s`. Full suite passed with `131 passed, 1 warning in 4.95s`. Secret scan passed. Preflight reported the new `Source live HTTP smoke` row and correctly failed it on this host because no supported Python 3.10-3.12 runtime was found. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This is still source-server validation. It does not replace package smoke helpers for macOS or Windows.

## Status update - 2026-06-23 06:32 -04:00
- **Now:** Upstream divergence has a repeatable local report and a written disposition artifact.
- **Next:** Use `.\tools\upstream_reconciliation.ps1` before any integration branch or remote-delta acceptance decision.
- **Blockers:** The Git graph is still behind `origin/main`; this pass documents and gates the delta but does not merge it.

### Upstream Reconciliation Report - Added
- **Done when:** Remaining upstream-only work is visible without running a pull or mutating the dirty roadmap worktree.
- **What changed:** Added `UPSTREAM_RECONCILIATION.md` and `tools/upstream_reconciliation.ps1`. Release preflight now requires both artifacts and parses the helper.
- **Tests run:** PowerShell parser checks for `tools/upstream_reconciliation.ps1` and `tools/release_preflight.ps1`; `.\tools\upstream_reconciliation.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** The reconciliation helper reported `ahead=0; behind=10`, `42 changed/untracked path(s)`, and runtime-sensitive upstream deltas in `ReadOut.spec`, `config.py`, extension files, `main.py`, `main_app.py`, `server.py`, and `ui.py`. Focused release docs/tools checks passed with `15 passed in 0.11s`. Full suite passed with `133 passed, 1 warning in 4.87s`. Secret scan passed. Preflight passed the new required artifact and helper syntax checks, then intentionally failed Git upstream currency, Python 3.10-3.12, and `espeak-ng`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This report does not remove the upstream graph blocker. It makes the remaining delta reviewable and repeatable.

## Status update - 2026-06-23 06:33 -04:00
- **Now:** Architect sign-off is an explicit release preflight gate instead of only a checklist note.
- **Next:** Architect must check the required rows in `ARCHITECT_SIGNOFF.md`, then run `.\tools\architect_signoff_check.ps1`.
- **Blockers:** Current sign-off packet is still intentionally failing because no required rows are accepted yet.

### Architect Sign-off Gate - Added
- **Done when:** Release preflight fails until required Architect-owned roadmap decisions are explicitly accepted.
- **What changed:** Added `tools/architect_signoff_check.ps1`, linked it from the release docs, and made `tools/release_preflight.ps1` run it in quiet mode.
- **Tests run:** PowerShell parser checks for `tools/architect_signoff_check.ps1` and `tools/release_preflight.ps1`; `.\tools\architect_signoff_check.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** The standalone sign-off checker reported each required row as `FAIL | Accept is not checked`, which matches the current unsigned packet. Focused release docs/tools checks passed with `16 passed in 0.10s`. Full suite passed with `134 passed, 1 warning in 5.14s`. Secret scan passed. Release preflight now requires and parses `tools/architect_signoff_check.ps1`, then reports `Architect sign-off | FAIL | architect_signoff_check.ps1 exit=1` alongside the known upstream/Python/espeak blockers. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This does not complete Architect-owned work. It makes the missing acceptance visible and release-blocking.

## Status update - 2026-06-23 06:34 -04:00
- **Now:** Target packaging evidence is an explicit release preflight gate.
- **Next:** Fill `PACKAGING_VALIDATION.md` on macOS and Windows targets, then run `.\tools\packaging_validation_check.ps1`.
- **Blockers:** The worksheet is still intentionally failing because all target validation rows remain `TBD`.

### Packaging Validation Gate - Added
- **Done when:** Release preflight fails until macOS and Windows packaging evidence is filled with concrete pass results or accepted gaps.
- **What changed:** Added `tools/packaging_validation_check.ps1`, linked it from the release docs, and made `tools/release_preflight.ps1` run it in quiet mode.
- **Tests run:** PowerShell parser checks for `tools/packaging_validation_check.ps1` and `tools/release_preflight.ps1`; `.\tools\packaging_validation_check.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** The standalone packaging checker reported every target row as failing because current results are `TBD` or `Pending`, which matches the unvalidated worksheet. Focused release docs/tools checks passed with `17 passed in 0.24s`. Full suite passed with `135 passed, 1 warning in 5.18s`. Secret scan passed. Release preflight now requires and parses `tools/packaging_validation_check.ps1`, then reports `Packaging validation evidence | FAIL | packaging_validation_check.ps1 exit=1` alongside the known upstream/Python/espeak/sign-off blockers. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This does not run package builds. It prevents the release checklist from treating blank target evidence as complete.

## Status update - 2026-06-23 06:35 -04:00
- **Now:** Release gate scripts have behavioral pytest coverage with real PowerShell execution against pass/fail fixtures.
- **Next:** Use the same gates on the target release machines after sign-off and package builds.
- **Blockers:** Behavioral coverage is green, but current sign-off and packaging worksheet state still intentionally fails.

### Release Gate Behavioral Coverage - Added
- **Done when:** Sign-off and packaging evidence gates are verified by execution, not only static string checks.
- **What changed:** Added behavioral tests for `tools/architect_signoff_check.ps1` and `tools/packaging_validation_check.ps1`, using repo-local temporary fixtures that are cleaned after the test. Tightened packaging validation so `PASS` rows require evidence/notes, and made macOS/Windows lifecycle rows distinct.
- **Tests run:** PowerShell parser checks for release gate scripts; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\architect_signoff_check.ps1`; `.\tools\packaging_validation_check.ps1`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** Focused release docs/tools checks passed with `19 passed in 18.34s`. Full suite passed with `137 passed, 1 warning in 21.89s`. Current standalone sign-off check still fails because Accept boxes are unchecked. Current standalone packaging validation still fails because target evidence rows are `TBD` or `Pending`. Secret scan passed. Preflight summarizes all expected failures, including upstream currency, Python 3.10-3.12, `espeak-ng`, Architect sign-off, and packaging evidence. `git diff --check` reported no whitespace errors, only CRLF conversion warnings. Temporary release-gate test directories were absent after the test run.
- **Notes / risks:** This improves release-gate reliability but does not replace Architect acceptance or target package validation.

## Status update - 2026-06-23 06:36 -04:00
- **Now:** Interactive manual smoke evidence is an explicit release preflight gate.
- **Next:** Fill `MANUAL_SMOKE_VALIDATION.md` on the intended release machine, then run `.\tools\manual_smoke_check.ps1`.
- **Blockers:** The worksheet is still intentionally failing because all interactive smoke rows remain `TBD`.

### Manual Smoke Validation Gate - Added
- **Done when:** Release preflight fails until source `/control`, Tk desktop, audible preview, and Chrome extension runtime smoke evidence is filled with concrete pass results or accepted gaps.
- **What changed:** Added `MANUAL_SMOKE_VALIDATION.md` and `tools/manual_smoke_check.ps1`, linked them from release docs, and made `tools/release_preflight.ps1` run the checker in quiet mode. Added behavioral pass/fail fixture coverage for the manual smoke checker.
- **Tests run:** PowerShell parser checks for `tools/manual_smoke_check.ps1` and `tools/release_preflight.ps1`; `.\tools\manual_smoke_check.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** The standalone manual smoke checker reported all interactive rows as failing because current results are `TBD` or `Pending`. Focused release docs/tools checks passed with `22 passed in 36.25s`. Full suite passed with `140 passed, 1 warning in 34.48s`. Secret scan passed. Release preflight now requires and parses `tools/manual_smoke_check.ps1`, then reports `Manual smoke evidence | FAIL | manual_smoke_check.ps1 exit=1` alongside known upstream/Python/espeak/sign-off/packaging blockers. `git diff --check` reported no whitespace errors, only CRLF conversion warnings. Temporary release-gate test directories were absent after the test run.
- **Notes / risks:** This does not perform interactive smoke tests. It prevents the release checklist from treating blank manual smoke evidence as complete.

## Status update - 2026-06-23 06:37 -04:00
- **Now:** Current roadmap blockers can be summarized from one non-mutating command.
- **Next:** Use `.\tools\roadmap_audit.ps1` before handing the packet to Architect or before target packaging runs.
- **Blockers:** The audit correctly fails until upstream currency, supported Python, `espeak-ng`, Architect sign-off, packaging evidence, and manual smoke evidence are resolved.

### Roadmap Audit Helper - Added
- **Done when:** A single local command summarizes the remaining roadmap gates without fetching, merging, building, launching GUI apps, or editing files.
- **What changed:** Added `tools/roadmap_audit.ps1`, linked it from README, `RELEASE_CHECKLIST.md`, and `ROADMAP_STATUS.md`, and made release preflight require and parse it.
- **Tests run:** PowerShell parser checks for `tools/roadmap_audit.ps1` and `tools/release_preflight.ps1`; `.\tools\roadmap_audit.ps1`; `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`; `python -m pytest`; `.\tools\secret_scan.ps1`; `.\tools\release_preflight.ps1`; `git diff --check`
- **Evidence:** The roadmap audit reported `Roadmap item coverage | PASS`, then failed the expected current blockers: upstream graph behind by 10, no supported Python 3.10-3.12, no `espeak-ng`, missing Architect sign-off, missing packaging validation, and missing manual smoke validation. Focused release docs/tools checks passed with `24 passed in 35.35s`. Full suite passed with `142 passed, 1 warning in 35.44s`. Secret scan passed. Release preflight now requires and parses `tools/roadmap_audit.ps1` while still failing the known release blockers. `git diff --check` reported no whitespace errors, only CRLF conversion warnings.
- **Notes / risks:** This summarizes blocker state; it does not complete external sign-off or target validation.

## Status update - 2026-06-23 13:35 -04:00
- **Now:** Roadmap work is reconciled onto clean branch `roadmap-integration` from `origin/main`; the upstream graph blocker is cleared in this worktree.
- **Next:** Resolve target packaging prerequisites or run validation on machines that already have them.
- **Tests:** `python -m pytest` passed with `142 passed, 1 warning in 37.11s`; release docs/tool checks passed with `24 passed in 30.17s`; `.\tools\secret_scan.ps1` passed; `git diff --check` passed with CRLF warnings only.
- **Blockers:** This Windows host still has only Python 3.13 registered by `py -0p`, no `espeak-ng` on PATH, and no `dist\ReadOut\ReadOut.exe` or `dist/ReadOut.app` package artifacts. Architect sign-off, packaging worksheet evidence, and manual smoke worksheet evidence remain intentionally failing gates.
- **Decisions needed (Architect):** P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4.

### Upstream Integration Worktree - Verified
- **Done when:** The roadmap implementation is based on the current remote branch instead of a stale dirty local checkout.
- **What changed:** Created/used `C:\Users\digit\Desktop\github-davehomeassist\readout-roadmap-integration` on branch `roadmap-integration`, based on `origin/main`, then ported the roadmap implementation and release artifacts into that clean branch.
- **Tests run:**
  - `git rev-list --left-right --count HEAD...origin/main`
  - `python -m pytest`
  - `python -m pytest tests/test_release_docs.py tests/test_release_tools.py`
  - `.\tools\secret_scan.ps1`
  - `.\tools\roadmap_audit.ps1`
  - `.\tools\release_preflight.ps1`
  - `git diff --check`
- **Evidence:** Git graph reported `0 0` against `origin/main`. Full test suite passed with `142 passed, 1 warning in 37.11s`. Roadmap audit now reports `Upstream graph | PASS | ahead=0; behind=0 vs origin/main`; it still fails on Python 3.10-3.12, `espeak-ng`, Architect sign-off, packaging validation, and manual smoke validation. Release preflight reports required files, PowerShell syntax, Git upstream currency, and secret scan as PASS, then fails the same remaining prerequisite/evidence gates.
- **Notes / risks:** The original dirty local `main` worktree remains separate and should not be blindly pulled, merged, reset, or overwritten.

### P3-A2 - Windows Packaging Host Preflight Rechecked
- **Done when:** Windows packaging prerequisites and package artifacts are current-state verified before attempting a build.
- **What changed:** Added `tools/windows_packaging_prereqs.ps1`, a non-mutating prerequisite report that checks supported Python, `espeak-ng`, and existing Windows package artifacts without creating a venv, installing dependencies, running PyInstaller, or launching the app. Rechecked local runtime availability and package outputs from the integration worktree.
- **Tests run:**
  - `py -0p`
  - `Get-Command espeak-ng -ErrorAction SilentlyContinue`
  - `Test-Path dist\ReadOut\ReadOut.exe`
  - `.\tools\windows_packaging_prereqs.ps1`
  - `.\tools\release_preflight.ps1`
- **Evidence:** `py -0p` reported only `-3.13-64`; `Get-Command espeak-ng` returned no path; `Test-Path dist\ReadOut\ReadOut.exe` returned `False`; `.\tools\windows_packaging_prereqs.ps1` reported FAIL for Python 3.10-3.12, `espeak-ng on PATH`, and existing Windows package; release preflight failed `Python 3.10-3.12` and `espeak-ng on PATH` while passing required file, syntax, Git upstream currency, and secret-scan checks.
- **Notes / risks:** No Windows package build was attempted because the build script is designed to fail before dependency install when supported Python or `espeak-ng` is absent. This is the correct show-safe behavior for release packaging.
- **Follow-ups:** Install Python 3.12/3.11/3.10 and `espeak-ng`, then run `.\build_windows.ps1` and `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe`.

## Status update - 2026-06-23 14:48 -04:00
- **Now:** Source-only live API/control and CORS evidence was refreshed without installers, package builds, audio playback, or GUI launch.
- **Next:** Keep target packaging, manual interactive smoke, and Architect acceptance as separate release blockers.
- **Tests:** Temporary Uvicorn server passed `.\tools\server_smoke.ps1` and `.\tools\cors_origin_matrix.ps1`.
- **Blockers:** Python 3.10-3.12, `espeak-ng`, packaged app artifacts, package smoke evidence, manual smoke evidence, and Architect sign-off remain unresolved.

### Source Live Server/CORS Evidence - Refreshed
- **Done when:** Non-audio source-server checks prove the local API, browser control surface, and exact-origin CORS behavior still work on the integration branch.
- **What changed:** No product code changed. The evidence log and Architect packet were updated to record the current source-only proof and remove stale upstream-blocker wording from the sign-off packet.
- **Tests run:**
  - Temporary `python -m uvicorn server:app --host 127.0.0.1 --port 7778 --log-level warning`
  - `.\tools\server_smoke.ps1 -BaseUrl http://127.0.0.1:7778`
  - `.\tools\cors_origin_matrix.ps1 -BaseUrl http://127.0.0.1:7778`
- **Evidence:** Server smoke passed `GET /status`, `GET /voices`, `GET /history`, and `GET /control`; `/status` returned `dependency_issues=3`, matching the known local prerequisite gaps. CORS matrix passed no-origin status, allowed local status, allowed local config preflight, blocked evil status, and blocked evil stop. The temporary Uvicorn process was stopped after the checks.
- **Notes / risks:** This is not package smoke evidence and does not prove audible Preview Voice, Speak, Save WAV, Stop playback, Tk desktop, Chrome extension, macOS app lifecycle, or Windows `ReadOut.exe` lifecycle.

## Status update - 2026-06-23 14:54 -04:00
- **Now:** Release Git verifiers handle this Windows checkout's Git ownership protection without requiring global `safe.directory` config.
- **Next:** Resolve the same real target blockers: supported Python, `espeak-ng`, package artifacts, package smoke, manual smoke, and Architect sign-off.
- **Tests:** Release docs/tool tests passed; upstream reconciliation, roadmap audit, and release preflight now report Git state correctly.
- **Blockers:** Packaging/sign-off/manual evidence remains intentionally failing.

### Release Git Verifiers - Hardened
- **Done when:** Roadmap/release helpers can inspect Git state from this checkout without misreporting the repo as unavailable or requiring a global machine config change.
- **What changed:** `tools/release_preflight.ps1`, `tools/roadmap_audit.ps1`, and `tools/upstream_reconciliation.ps1` now pass a command-local `safe.directory` for the current repo. `tools/upstream_reconciliation.ps1` now reports only upstream-side file deltas with `HEAD...origin/main`, so local roadmap commits are not mislabeled as upstream changes.
- **Tests run:**
  - `python -m pytest tests/test_release_tools.py tests/test_release_docs.py`
  - `.\tools\upstream_reconciliation.ps1`
  - `.\tools\roadmap_audit.ps1`
  - `.\tools\release_preflight.ps1`
- **Evidence:** Focused release docs/tool tests passed with `25 passed in 30.99s`. Upstream reconciliation reported `Graph | PASS | ahead=2; behind=0`, `Runtime-sensitive upstream paths | PASS`, and no upstream-only commits or file delta. Roadmap audit reported `Upstream graph | PASS | ahead=2; behind=0 vs origin/main`, then failed only the known Python/espeak/sign-off/packaging/manual evidence gates. Release preflight reported `Git upstream currency | PASS | ahead=0; behind=0 vs origin/roadmap-integration`, then failed the same known release blockers.
- **Notes / risks:** This hardens the verifiers only. It does not install prerequisites, create package artifacts, accept Architect decisions, or perform interactive manual smoke.

## Status update - 2026-06-23 15:01 -04:00
- **Now:** A manual GitHub Actions package-smoke workflow exists so Windows/macOS package builds and non-audio smoke checks can run on suitable hosted runners instead of this under-provisioned workstation.
- **Next:** Trigger the `package-smoke` workflow, review uploaded evidence artifacts, then fill `PACKAGING_VALIDATION.md` with the real results.
- **Tests:** Release docs/tool tests passed; local roadmap audit still fails only the known external evidence/sign-off/prerequisite gates.
- **Blockers:** Workflow evidence has not been produced yet; manual tray/audio/extension evidence and Architect sign-off are still required.

### Hosted Package Smoke Workflow - Added
- **Done when:** The repo has a repeatable CI path that can build Windows and macOS packages with Python 3.12 and `espeak-ng`, run the existing package smoke helpers, and upload artifacts for the packaging worksheet.
- **What changed:** Added `.github/workflows/package-smoke.yml` as a manual `workflow_dispatch` workflow with separate Windows and macOS jobs. The Windows job installs eSpeak NG through WinGet, runs `build_windows.ps1`, runs `tools/windows_package_smoke.ps1`, and uploads the package/log/smoke evidence. The macOS job installs `espeak-ng` through Homebrew, runs `build_mac.sh`, runs `tools/mac_package_smoke.sh`, archives `ReadOut.app`, and uploads package/log/smoke evidence.
- **Tests run:**
  - `python -m pytest tests/test_release_docs.py tests/test_release_tools.py`
  - `git diff --check`
  - `.\tools\roadmap_audit.ps1`
- **Evidence:** Focused release docs/tool tests passed with `26 passed in 34.28s`. `git diff --check` reported no whitespace errors, only CRLF conversion warnings. Roadmap audit reported upstream graph PASS and still failed the expected local Python/espeak/sign-off/packaging/manual evidence gates.
- **Notes / risks:** The workflow has not run yet. CI package smoke is non-audio and still does not replace manual tray/menu-bar visual confirmation, audible preview checks, Chrome extension smoke, or Architect acceptance unless an explicit accepted gap is recorded.

## Status update - 2026-06-23 15:31 -04:00
- **Now:** Hosted Windows and macOS package builds plus non-audio package smoke checks passed on GitHub Actions for commit `b2f02cee11ff6340ad5fcec51db4bb29e2856fdc`.
- **Next:** Complete manual visible tray/menu-bar and audible preview/speak/stop smoke evidence, or have the Architect explicitly accept those gaps.
- **Tests:** GitHub Actions package-smoke run `28051156266` passed; tests workflow run `28051156286` passed Python 3.10, 3.11, and 3.12 jobs.
- **Blockers:** Architect sign-off, manual smoke worksheet, macOS visible tray/menu-bar verification, and audible lifecycle evidence remain required.

### Hosted Package Smoke Evidence - Recorded
- **Done when:** Windows and macOS hosted runners build package artifacts with Python 3.12 and `espeak-ng`, run packaged app server/control/CORS smoke, and upload evidence artifacts.
- **What changed:** `PACKAGING_VALIDATION.md` and `ROADMAP_STATUS.md` now record the successful package-smoke run, artifact IDs, and remaining manual-only gaps. `tools/roadmap_audit.ps1` now treats filled hosted/target evidence for Python 3.10-3.12 and `espeak-ng` as satisfying those roadmap prerequisite rows, so local workstation gaps are not reported as release blockers unless packages must be built on this host.
- **Tests run:**
  - GitHub Actions `package-smoke` run `28051156266`
  - GitHub Actions tests workflow run `28051156286`
- **Evidence:** Run `28051156266` passed overall at head `b2f02cee11ff6340ad5fcec51db4bb29e2856fdc`. Windows job `83041801593` built `dist\ReadOut\ReadOut.exe`, reported `Executable exists PASS`, `Server ready PASS`, `Non-audio server smoke PASS`, `CORS origin matrix PASS`, and `Stop packaged exe PASS`, then uploaded artifact `readout-windows-package-smoke` id `7831258309` with digest `sha256:6bfa7ce5974e8f13bdf335e4b1e967ea8efdff6dec04d213e3e4d2980a91f57d`. macOS job `83041801690` built `dist/ReadOut.app` size `593M`, reported `App bundle exists PASS`, `Launch packaged app PASS`, `Server ready PASS`, `/status`, `/voices`, `/history`, `/control`, and blocked-origin checks PASS, then uploaded artifact `readout-macos-package-smoke` id `7831229443` with digest `sha256:26bdd209799a0dd36eda66efcbd985d7b6a26c0c2c4242c6c66b37299462d335`. Tests run `28051156286` passed Python 3.10, 3.11, and 3.12 jobs on the same head SHA. `.\tools\roadmap_audit.ps1` now reports Python 3.10-3.12 PASS and `espeak-ng` PASS from hosted/target evidence, then still fails Architect sign-off, packaging validation, and manual smoke validation.
- **Notes / risks:** This clears the hosted Python/`espeak-ng` package-build path. It does not prove visible macOS tray/menu-bar behavior, audible preview/speak/stop lifecycle, Chrome extension manual smoke, or Architect acceptance.

## Status update - 2026-06-23 15:55 -04:00
- **Now:** The next executor handoff is captured in `NEXT_EXECUTOR_PROMPT.md`.
- **Next:** Use the prompt to complete Architect sign-off, packaging manual rows, and interactive manual smoke without repeating the completed hosted package-smoke prerequisite work.
- **Tests:** Full suite passed with `145 passed, 1 warning in 37.55s`; focused release docs/tool tests passed with `27 passed in 31.32s`; `git diff --check` passed with CRLF warnings only.
- **Blockers:** Same remaining owner/manual gates: Architect sign-off, packaging manual rows, and manual smoke worksheet evidence.

### Next Executor Handoff - Added
- **Done when:** The next executor can start from the current source-of-truth evidence and open rows without rediscovering the old Python/`espeak-ng` package blocker.
- **What changed:** Added `NEXT_EXECUTOR_PROMPT.md`, linked it from README and `RELEASE_CHECKLIST.md`, and made release preflight require it as a tracked release artifact. `tools/release_preflight.ps1` now also accepts recorded hosted/target Python and `espeak-ng` evidence, matching `tools/roadmap_audit.ps1`.
- **Evidence:** The prompt names the successful package-smoke run `28051156266`, tests run `28051156286`, the exact remaining worksheet rows, and the final commands required before reporting green. `.\tools\release_preflight.ps1` now reports Python 3.10-3.12 PASS and `espeak-ng on PATH` PASS from hosted/target evidence, then still fails only Architect sign-off, packaging validation, and manual smoke evidence.
- **Notes / risks:** This is a handoff/control artifact only. It does not complete Architect acceptance or manual smoke validation.

## Status update - 2026-06-23 16:00 -04:00
- **Now:** Architect sign-off packet has been brought current with the hosted package-smoke evidence.
- **Next:** Architect can review the actual remaining release risks: manual macOS tray/audio evidence, Windows audible lifecycle evidence, source `/control`, Tk desktop, and Chrome extension manual smoke.
- **Tests:** Focused release docs/tool tests passed with `27 passed in 31.79s`; `git diff --check` passed with CRLF warnings only; `.\tools\architect_signoff_check.ps1` failed only because required Accept boxes are unchecked; `.\tools\roadmap_audit.ps1` still fails only Architect sign-off, packaging validation, and manual smoke validation.
- **Blockers:** Architect acceptance and manual smoke evidence remain incomplete.

### Architect Packet Stale Blocker Cleanup - Added
- **Done when:** `ARCHITECT_SIGNOFF.md` no longer asks the Architect to treat Python, `espeak-ng`, or package artifact creation as unresolved when hosted evidence already exists.
- **What changed:** Updated `ARCHITECT_SIGNOFF.md` current-blocker language to cite hosted package-smoke run `28051156266` and list only the remaining manual visual/audio/smoke gaps.
- **Evidence:** The packet now points to `PACKAGING_VALIDATION.md` for package artifacts and non-audio smoke evidence, while keeping the manual rows and Architect acceptance as release-blocking.
- **Notes / risks:** This does not sign the packet or fill manual smoke evidence.

## Status update - 2026-06-23 17:54 -04:00
- **Now:** A stateful non-audio source `/control` workflow smoke helper exists.
- **Next:** Run it with ReadOut running to capture backend evidence for status refresh, history toggle/clear, and stop before the remaining human audio/desktop/extension checks.
- **Tests:** Full suite passed with `146 passed, 1 warning in 42.00s`; focused release docs/tool tests passed with `28 passed in 37.33s`; `git diff --check` passed with CRLF warnings only; PowerShell parser check for `tools/control_workflow_smoke.ps1` passed; live temporary Uvicorn smoke passed. `.\tools\roadmap_audit.ps1` and `.\tools\release_preflight.ps1` still fail only Architect sign-off, packaging validation, and manual smoke evidence.
- **Blockers:** Manual audible playback, Tk desktop, Chrome extension smoke, package manual rows, and Architect acceptance remain incomplete.

### Source Control Workflow Smoke Helper - Added
- **Done when:** The source `/control` backend workflow can be exercised without audio and without leaving local config/history mutated.
- **What changed:** Added `tools/control_workflow_smoke.ps1`, linked it from README, `RELEASE_CHECKLIST.md`, `NEXT_EXECUTOR_PROMPT.md`, and release preflight required-file/syntax checks.
- **Evidence:** The helper checks `/status`, `/control`, `PATCH /config` history controls, `GET/DELETE /history`, and `POST /stop`, then restores local `~/.readout/config.json` and `history.json` byte-for-byte. A temporary local server on `127.0.0.1:7784` passed all helper rows: loopback target, status refresh backend, control panel backend page, history toggle via config, history status refresh, Clear History backend, Stop backend, and Restore local config/history.
- **Notes / risks:** This does not prove audible preview/speak/save, visible tray/menu-bar behavior, Tk desktop interaction, or Chrome extension behavior.

## Status update - 2026-06-23 17:58 -04:00
- **Now:** A Chrome extension static release smoke helper exists.
- **Next:** Run it before manual Chrome smoke so manifest, permission, endpoint, context-menu, and popup contracts are checked without launching Chrome.
- **Tests:** Full suite passed with `147 passed, 1 warning in 35.27s`; `.\tools\extension_static_smoke.ps1` passed; focused release docs/tools/extension popup tests passed with `33 passed in 31.97s`; `git diff --check` passed with CRLF warnings only; `.\tools\roadmap_audit.ps1` and `.\tools\manual_smoke_check.ps1` still fail only the expected Architect/manual evidence gates.
- **Blockers:** Chrome runtime popup/audio behavior, manual audible playback, package manual rows, and Architect acceptance remain incomplete.

### Extension Static Smoke Helper - Added
- **Done when:** The extension release contract can be checked without Chrome or network access.
- **What changed:** Added `tools/extension_static_smoke.ps1`, linked it from README, `RELEASE_CHECKLIST.md`, `NEXT_EXECUTOR_PROMPT.md`, release preflight required-file/syntax checks, and manual smoke support evidence.
- **Evidence:** The helper checks Manifest V3, least-privilege permissions, exact localhost host permission, popup/default icon files, popup status and preview controls, popup endpoint wiring, context-menu IDs, `/speak` and `/stop` wiring, and content-script toast wiring. It passed all rows on 2026-06-23 17:58 -04:00.
- **Notes / risks:** This does not prove the extension can be loaded in Chrome, that the extension origin is allowlisted, that popup READY/OFFLINE paths render at runtime, or that audio playback works.

## Status update - 2026-06-23 18:05 -04:00
- **Now:** Release preflight executes the safe extension static smoke by default and can run the stateful `/control` workflow smoke under `-RunLiveChecks`.
- **Next:** Continue to use manual smoke worksheets for actual Chrome runtime, audible playback, desktop, and package visual checks.
- **Tests:** Full suite passed with `147 passed, 1 warning in 35.00s`; `.\tools\release_preflight.ps1` now reports `Extension static smoke | PASS`; `.\tools\release_preflight.ps1 -BaseUrl http://127.0.0.1:7787 -RunLiveChecks` reports `Live server smoke | PASS`, `Live CORS matrix | PASS`, and `Live control workflow smoke | PASS`; focused release docs/tools/extension popup tests passed with `33 passed in 31.16s`; `git diff --check` passed with CRLF warnings only; `.\tools\roadmap_audit.ps1` still fails only the expected Architect sign-off, packaging validation, and manual smoke gates.
- **Blockers:** Architect acceptance, package manual rows, and manual smoke evidence remain incomplete.

### Release Preflight Smoke Wiring - Added
- **Done when:** Safe non-interactive smoke helpers are part of the standard release preflight instead of only being listed as required files.
- **What changed:** `tools/release_preflight.ps1` now runs `tools/extension_static_smoke.ps1` by default and reports `Extension static smoke`; `-RunLiveChecks` now also runs `tools/control_workflow_smoke.ps1` and reports `Live control workflow smoke`.
- **Evidence:** A temporary Uvicorn server on `127.0.0.1:7787` passed the preflight live server smoke, CORS matrix, and control workflow smoke rows. Preflight still correctly fails Architect sign-off, packaging validation evidence, and manual smoke evidence.
- **Notes / risks:** `Live control workflow smoke` remains opt-in because it requires a running local ReadOut server and temporarily mutates local config/history before restoring them.

## Status update - 2026-06-23 18:11 -04:00
- **Now:** Release preflight treats upstream reconciliation as a first-class release gate instead of only checking that the helper file exists.
- **Next:** Complete the same remaining owner/manual gates: Architect sign-off, package manual visual/audio rows, and interactive manual smoke evidence.
- **Tests:** Focused release docs/tool tests passed with `29 passed in 30.71s`; full suite passed with `147 passed, 1 warning in 35.30s`; `git diff --check` passed with CRLF warnings only.
- **Blockers:** Architect sign-off, packaging validation evidence, and manual smoke evidence remain intentionally failing.

### Release Preflight Upstream Gate - Added
- **Done when:** The release preflight reports whether the integration branch is clean and reconciled with `origin/main`, using the same dedicated upstream helper named in the release checklist.
- **What changed:** `tools/upstream_reconciliation.ps1` now supports `-Quiet` and exits nonzero for `REVIEW` rows. `tools/release_preflight.ps1` now calls it with `-UpstreamRef origin/main` and reports `Upstream reconciliation` separately from branch tracking currency.
- **Evidence:** `.\tools\upstream_reconciliation.ps1` reports graph `PASS` with `ahead=14; behind=0` against `origin/main`; during the edit pass it correctly returned nonzero because the worktree had local changes. `.\tools\release_preflight.ps1` now prints `Upstream reconciliation` and preserves the known failing Architect/manual evidence rows. Focused and full pytest runs passed.
- **Notes / risks:** This is a release gate/reporting improvement only. It does not change app behavior, sign the Architect packet, or replace the remaining manual smoke worksheets.

## Status update - 2026-06-23 18:21 -04:00
- **Now:** Tk desktop source-contract smoke is automated and included in release preflight.
- **Next:** Still complete the manual desktop launch/audio row, Chrome runtime row, `/control` audio rows, packaging manual rows, and Architect sign-off.
- **Tests:** `.\tools\tk_desktop_static_smoke.ps1` passed all static Tk desktop rows; focused release/docs/UI tests passed with `40 passed in 30.44s`.
- **Blockers:** Architect sign-off, packaging validation evidence, and manual smoke evidence remain intentionally failing.

### Tk Desktop Static Smoke Helper - Added
- **Done when:** The Tk desktop source contract can be checked without launching a GUI or playing audio.
- **What changed:** Added `tools/tk_desktop_static_smoke.ps1`, wired it into `tools/release_preflight.ps1`, and linked it from README, release checklist, roadmap status, next-executor prompt, and manual smoke support evidence.
- **Evidence:** The helper passed Tk app class, localhost server target, supported engine tabs, no Browser engine tab, Preview Voice, Save WAV, play/stop controls, config persistence wiring, `/voices`, `/status`, `/preview`, `/speak`, `/stop`, and save-true payload checks.
- **Notes / risks:** This does not prove the Tk window opens on the target machine or that audible Preview Voice/Speak/Save WAV/Stop works. Those rows remain manual release gates.

## Status update - 2026-06-23 18:37 -04:00
- **Now:** Current-head hosted Windows and macOS package smoke evidence is recorded for commit `06369b46b3d929adcec1cba1c1ebc706a548b0c9`.
- **Next:** Complete only the remaining owner/manual gates: Architect sign-off, macOS visible tray/menu-bar and audible lifecycle rows, Windows audible lifecycle row, and the interactive source/Tk/Chrome manual smoke worksheet.
- **Tests:** GitHub Actions tests run `28061248462` passed Python 3.10, 3.11, and 3.12 jobs on the then-current package-producing head. GitHub Actions package-smoke run `28061318132` passed Windows job `83075924486` and macOS job `83075924465` on the same head.
- **Blockers:** No local Python or `espeak-ng` install is required unless the task changes to local workstation packaging. The release remains yellow because Architect sign-off, package manual visual/audio rows, and manual smoke evidence remain incomplete.

### Current-head Hosted Package Smoke Evidence - Refreshed
- **Done when:** Package evidence references the current integration head instead of an older package-smoke commit.
- **What changed:** Updated `PACKAGING_VALIDATION.md`, `ROADMAP_STATUS.md`, `ARCHITECT_SIGNOFF.md`, and `NEXT_EXECUTOR_PROMPT.md` to cite package-smoke run `28061318132` and tests run `28061248462`.
- **Evidence:** macOS job `83075924465` built `dist/ReadOut.app`, reported app bundle exists, launch, server ready, `/status`, `/voices`, `/history`, `/control`, and blocked-origin checks as PASS, and uploaded artifact `readout-macos-package-smoke` id `7835173905` with digest `sha256:0e9888702bbc65dbf766b3a7e0410cfb54197ef9c10eb3840beb4e28c8b545de`. Windows job `83075924486` built `dist\ReadOut\ReadOut.exe`, reported executable exists, launch, server ready, non-audio server smoke, CORS origin matrix, and process stop as PASS, and uploaded artifact `readout-windows-package-smoke` id `7835190908` with digest `sha256:7d13725b70c151c04c9b081e9881a3a44eacfb418b34730e93d092c4dbd5e3a4`.
- **Notes / risks:** Hosted package smoke is still non-audio/headless. It clears package prerequisite evidence for the package-producing head, but it does not prove audible preview/speak/stop, visible macOS tray/menu-bar controls, Tk/Chrome manual runtime behavior, or Architect acceptance.

## Status update - 2026-06-23 18:54 -04:00
- **Now:** macOS package smoke now asserts clean quit and hosted package smoke passed at package-producing commit `440cb577875dfd2aad8a359df972471e5c207511`.
- **Next:** Complete only the remaining owner/manual gates: Architect sign-off, macOS visible menu-bar/tray and tray-to-control rows, macOS audible lifecycle row, Windows audible lifecycle row, and the interactive source/Tk/Chrome manual smoke worksheet.
- **Tests:** Local focused release docs/tool tests passed with `30 passed in 30.50s`; push tests run `28062313482` passed Python 3.10, 3.11, and 3.12; package-smoke run `28062313500` passed Windows and macOS.
- **Blockers:** No local Python or `espeak-ng` install is required unless the task changes to local workstation packaging. The release remains yellow because Architect sign-off, package manual visual/audio rows, and manual smoke evidence remain incomplete.

### macOS Package Clean Quit Evidence - Added
- **Done when:** The macOS package smoke helper proves the packaged app exits cleanly after launch/server/control checks.
- **What changed:** `tools/mac_package_smoke.sh` now resolves the app executable, watches for the ReadOut process to disappear after `osascript` quit, verifies the local server no longer responds, and emits an `App quits cleanly` PASS/FAIL row. `PACKAGING_VALIDATION.md`, `ROADMAP_STATUS.md`, `ARCHITECT_SIGNOFF.md`, and `NEXT_EXECUTOR_PROMPT.md` now cite the refreshed package-producing evidence.
- **Evidence:** macOS job `83079089516` in run `28062313500` built `dist/ReadOut.app`, passed app bundle, launch, server ready, `/status`, `/voices`, `/history`, `/control`, blocked-origin, and `App quits cleanly PASS`; artifact `readout-macos-package-smoke` id `7835539633`, digest `sha256:e47d55b52e30355d306099d40016eaeb43f7a10b942c44f141ae8cfc5f278758`. Windows job `83079089531` passed and uploaded artifact `readout-windows-package-smoke` id `7835571251`, digest `sha256:143face540b9243b602fa9171cee3502ecfd40de194ffc7fdb7caa87df39cc17`.
- **Notes / risks:** This removes the clean-quit manual packaging row. It still does not prove visible macOS menu-bar/tray behavior, tray menu selection, audible preview/speak/stop lifecycle, Chrome runtime behavior, Tk manual launch/audio, or Architect acceptance.

## Status update - 2026-06-23 19:12 -04:00
- **Now:** Architect sign-off is transcribed from the canonical Notion Architect page into `ARCHITECT_SIGNOFF.md`; `tools/architect_signoff_check.ps1` passes.
- **Next:** Complete only package manual visual/audio rows and the interactive manual smoke worksheet, or record explicit accepted gaps.
- **Tests:** `.\tools\architect_signoff_check.ps1` passed all required rows. Focused release docs/tool tests passed with `30 passed in 33.70s`. `.\tools\packaging_validation_check.ps1` now passes Architect/precondition/P3-A4 rows and fails only macOS menu-bar/tray, tray Open Control Panel, macOS audible lifecycle, Windows audible lifecycle, and P3-A1/P3-A2 summaries. `.\tools\roadmap_audit.ps1` now reports Architect sign-off PASS and still fails packaging/manual smoke.
- **Blockers:** Package manual visual/audio evidence and manual smoke evidence remain incomplete. No local Python or `espeak-ng` install is required unless the task changes to local workstation packaging.

### Architect Sign-off Gate - Cleared
- **Done when:** The repo-local Architect worksheet reflects the existing Architect decisions and the checker passes without clearing package/manual smoke.
- **What changed:** `ARCHITECT_SIGNOFF.md`, `DECISION_LOG.md`, `ROADMAP_STATUS.md`, `PACKAGING_VALIDATION.md`, and `NEXT_EXECUTOR_PROMPT.md` now record the accepted Architect decisions from the Notion Architect sign-off page. `tools/roadmap_audit.ps1` now prints a pass-appropriate next action for cleared gates.
- **Evidence:** `.\tools\architect_signoff_check.ps1` reports PASS for P0-A4, P1-A2, P1-A4, P1-A5, P2-A1, P2-A4, and P3-A4. Packaging and manual smoke checkers still fail the remaining target/manual rows, so release status remains yellow.
- **Notes / risks:** This clears the Architect decision gate only. It does not replace target machine visual checks or audible playback/manual smoke evidence.

## Status update - 2026-06-23 19:23 -04:00
- **Now:** Current-facing release docs explicitly keep Python 3.10-3.12 and `espeak-ng` out of the open-blocker list unless local workstation packaging is explicitly requested or package/runtime source changes invalidate hosted evidence.
- **Next:** Finish package manual visual/audio evidence and interactive manual smoke rows, or record accepted gaps.
- **Tests:** Focused release docs/tool tests passed with `30 passed in 30.18s`; `tools/roadmap_audit.ps1` still fails only packaging validation and manual smoke validation; `tools/release_preflight.ps1` still fails upstream reconciliation while the worktree is dirty plus the known package/manual evidence gates.
- **Blockers:** Package manual visual/audio evidence and manual smoke evidence remain incomplete.

### Hosted Prerequisite Scope - Clarified
- **Done when:** The next executor does not repeat local installer work for prerequisite rows already satisfied by hosted package-smoke evidence.
- **What changed:** `README.md`, `RELEASE_CHECKLIST.md`, and `NEXT_EXECUTOR_PROMPT.md` now distinguish target/hosted Python and `espeak-ng` evidence from local workstation setup.
- **Evidence:** Package-smoke run `28062313500` and tests run `28062313482` remain the source of truth for Python 3.10-3.12 and `espeak-ng` package prerequisite rows.
- **Notes / risks:** This is documentation scope control only; it does not clear package manual visual/audio or manual smoke gates.

## Status update - 2026-06-23 19:30 -04:00
- **Now:** Two source `/control` non-audio rows have direct current evidence on the real `127.0.0.1:7778` port.
- **Next:** Finish the remaining source audio/status/stop-during-playback rows, Tk desktop smoke, Chrome extension runtime smoke, and package manual visual/audio rows.
- **Tests:** Full suite passed with `148 passed, 1 warning in 34.96s`; focused release docs/tool tests passed with `30 passed in 30.52s`; `.\tools\manual_smoke_check.ps1` now reports PASS for `/control` opens and `/control` history toggle/Clear History while still failing the unproven manual rows; `.\tools\roadmap_audit.ps1` still fails only packaging/manual smoke gates; `git diff --check` passed with CRLF warnings only.
- **Blockers:** Package manual visual/audio evidence and most manual smoke rows remain incomplete.

### Source Control Non-Audio Evidence - Refreshed
- **Done when:** Source `/control` opens and history enable/clear behavior are backed by a current live source-server run on the actual release port.
- **What changed:** `MANUAL_SMOKE_VALIDATION.md` now records PASS evidence for `/control` opening on `127.0.0.1:7778` and the source `/control` history toggle/Clear History backend workflow. `NEXT_EXECUTOR_PROMPT.md` now names the remaining source `/control` manual rows instead of asking the next executor to redo the whole section.
- **Evidence:** Temporary source server on `127.0.0.1:7778` reported `SERVER_READY status=ready; engine=kokoro; dependency_issues=3`. `.\tools\server_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed `/status`, `/voices`, `/history`, and `/control`. `.\tools\control_workflow_smoke.ps1 -BaseUrl http://127.0.0.1:7778` passed loopback target, status refresh backend, control panel backend page, history toggle via config, history status refresh, Clear History backend, Stop backend, and byte-preserving local config/history restore.
- **Notes / risks:** This does not prove browser-rendered status display updates, audible preview/speak/save/stop behavior, Tk desktop launch/audio, Chrome extension runtime behavior, or package tray/menu-bar/audio rows.

## Status update - 2026-06-23 19:40 -04:00
- **Now:** Tk desktop launch and engine/voice/speed config persistence have current runtime evidence on this Windows workstation.
- **Next:** Finish remaining audible Tk rows, source `/control` status/audio/save/stop rows, Chrome extension runtime rows, and package manual visual/audio rows.
- **Tests:** `.\tools\tk_desktop_runtime_smoke.ps1` passed all rows and restored local config/history; focused release docs/tool tests passed with `31 passed in 40.00s`; full suite passed with `149 passed, 1 warning in 36.00s`; `.\tools\manual_smoke_check.ps1` now reports PASS for source `/control` open/history and Tk desktop open/config rows while still failing the remaining unproven manual rows; `git diff --check` passed with CRLF warnings only.
- **Blockers:** Package manual visual/audio evidence and remaining manual audio/runtime rows remain incomplete.

### Tk Desktop Runtime Smoke Helper - Added
- **Done when:** The Tk desktop can be opened on a desktop-capable Windows target and its non-audio backend config workflow can be verified without leaving local config/history mutated.
- **What changed:** Added `tools/tk_desktop_runtime_smoke.ps1`, wired it into release preflight required-file/syntax checks, README, release checklist, roadmap status, next executor prompt, manual smoke evidence, and release tests. `MANUAL_SMOKE_VALIDATION.md` now records PASS evidence for Tk desktop opening and desktop engine/voice/speed persistence.
- **Evidence:** `.\tools\tk_desktop_runtime_smoke.ps1` passed Port available, Launch source server, Server ready, Tk window opens (`560x680` on `1920x1080` screen), Tk controls present, Desktop engine persists (`openai`/`alloy`), Desktop voice persists (`nova`), Desktop speed persists (`1.7`), Stop source server, and Restore local config/history.
- **Notes / risks:** This is a non-audio runtime smoke. It does not prove audible Preview Voice, Speak, Save WAV, Stop during playback, Chrome extension runtime behavior, or package tray/menu-bar/audio rows.

## Status update - 2026-06-23 19:53 -04:00
- **Now:** Source `/control` browser-rendered status display has current Chrome DOM evidence on this Windows workstation.
- **Next:** Finish remaining source `/control` audio/save/stop rows, audible Tk rows, Chrome extension runtime rows, and package manual visual/audio rows.
- **Tests:** `.\tools\control_browser_runtime_smoke.ps1` passed all rows; focused release docs/tool tests passed with `32 passed in 30.74s`; full suite passed with `150 passed, 1 warning in 35.25s`; clean-tree `.\tools\release_preflight.ps1` passed upstream reconciliation, required files/syntax, Python, hosted `espeak-ng`, secret scan, extension static smoke, Tk desktop static smoke, and Architect sign-off, then still failed packaging/manual evidence as expected; `.\tools\manual_smoke_check.ps1` now reports PASS for `/control` status display updates while still failing the remaining unproven manual rows; `git diff --check` passed with CRLF warnings only.
- **Blockers:** Package manual visual/audio evidence and remaining manual audio/runtime rows remain incomplete.

### Source Control Browser Runtime Smoke Helper - Added
- **Done when:** The `/control` page status display can be proven to update in a real Chromium renderer without claiming audible playback.
- **What changed:** Added `tools/control_browser_runtime_smoke.ps1`, wired it into release preflight required-file/syntax checks, README, release checklist, roadmap status, next executor prompt, manual smoke evidence, and release tests. `MANUAL_SMOKE_VALIDATION.md` now records PASS evidence for `/control` status display updates.
- **Evidence:** `.\tools\control_browser_runtime_smoke.ps1` started a temporary source server on `127.0.0.1:7778`, opened `/control` in headless Chrome, and verified `/control status display updates PASS` with rendered DOM `state=ready`, `label=Ready`, and updated feedback from `/status`.
- **Notes / risks:** This is a non-audio source-control browser smoke. It does not prove audible Preview Voice, Speak, Save WAV, Stop during playback, Chrome extension runtime behavior, or package tray/menu-bar/audio rows.

## Status update - 2026-06-23 21:07 -04:00
- **Now:** ReadOut runs on the local Python 3.12 venv with bundled `espeakng_loader`; source `/control` Save WAV/Stop has browser action evidence; local Windows package build and non-audio package smoke pass.
- **Next:** Finish human-audible source/Tk/Chrome rows, macOS tray/menu-bar rows, and Windows audible lifecycle evidence or record accepted gaps.
- **Tests:** Focused dependency/runtime/release tests passed with `55 passed in 33.75s`; `.\tools\control_browser_action_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe` passed all rows; `.\build_windows.ps1` completed; `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 120` passed; `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 120 -IncludeAudio` did not pass cleanly and is not counted as audio evidence.
- **Blockers:** Human-audible playback evidence remains incomplete for source `/control`, Tk desktop, Chrome extension, and packaged Windows/macOS. macOS package evidence is older than this runtime change and should be refreshed on macOS or explicitly accepted before final green.

### Bundled eSpeak Runtime + Windows Package Evidence - Added
- **Done when:** The app can use the bundled Python eSpeak runtime instead of forcing a global MSI, and local Windows packaging has current evidence.
- **What changed:** `tts_engine.py` now calls `espeakng_loader.make_library_available()` before importing Kokoro when the loader is available. `dependency_check.py`, `build_windows.ps1`, `tools/windows_packaging_prereqs.ps1`, and `tools/release_preflight.ps1` now accept either system `espeak-ng` or bundled `espeakng_loader`. `requirements.txt` explicitly includes `espeakng-loader`. Added `tools/control_browser_action_smoke.ps1` to click the rendered `/control` Save WAV and Stop buttons via headless Chrome DevTools and restore local config/history.
- **Evidence:** Dependency check inside `.venv` returned `[]`; Windows prereq report passed Python 3.12.10 and bundled `espeakng_loader`. Browser action smoke reported `Server ready PASS` with `dependency_issues=0`, clicked Save WAV, created `readout_1782262606.wav` at 231,644 bytes, clicked Stop, removed the smoke WAV, and restored local config/history. Local Windows build reported `espeak-ng: OK (bundled espeakng_loader)` and `Build complete: dist\ReadOut\ReadOut.exe`; local package smoke reported executable launch, server ready, `/status` with `dependency_issues=0`, `/control`, CORS matrix, and process stop PASS.
- **Notes / risks:** This proves source/package non-audio runtime, synthesis-to-WAV, and stop command plumbing. It still does not prove human-audible output on the speakers or Chrome extension runtime behavior.

## Status update - 2026-06-23 21:44 -04:00
- **Now:** Chrome extension popup runtime non-audio evidence exists for origin allowlist, OFFLINE/READY text, and Stop command plumbing.
- **Next:** Finish remaining human-audible rows: source `/control` Preview Voice/Speak text, Tk desktop Preview Voice and Speak/Save/Stop, Chrome extension Preview Voice audio and context-menu selected-text playback, plus package visual/audio rows or accepted gaps.
- **Tests:** `.\tools\extension_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe` passed all required rows; focused release/docs/extension tests passed with `39 passed in 37.94s`; full suite passed with `156 passed, 1 warning in 39.75s`; `tools/manual_smoke_check.ps1` now passes extension origin/READY/OFFLINE/Stop rows and still fails only remaining manual audio/context rows plus summaries; `tools/packaging_validation_check.ps1` still fails expected package visual/audio rows.
- **Blockers:** Human-audible playback evidence and package manual visual/audio evidence remain incomplete; the release stays yellow until `tools/manual_smoke_check.ps1` and `tools/packaging_validation_check.ps1` pass or accepted gaps are recorded.

### Chrome Extension Runtime Smoke Helper - Added
- **Done when:** The extension popup READY/OFFLINE/origin/Stop command paths can be verified in Chromium without playing audio or leaving local config/history mutated.
- **What changed:** Added `tools/extension_runtime_smoke.ps1`, refactored the popup Stop action into shared `stopPlayback()`, and hardened popup startup with explicit fetch timeouts and immediate status refresh. Wired the helper into release preflight required-file/syntax checks, README, release checklist, roadmap status, next executor prompt, manual smoke evidence, and regression tests.
- **Evidence:** The helper loaded the unpacked extension through Chromium DevTools `Extensions.loadUnpacked`, verified popup OFFLINE text before starting the server, started a temporary source server with `dependency_issues=0`, allowlisted the real `chrome-extension://...` origin, verified popup READY text for Kokoro/`af_heart`, ran `stopPlayback()` and observed `Stop sent to ReadOut.`, then stopped the server/browser and restored local config/history.
- **Notes / risks:** Chrome on this host did not expose tab targets for `Extensions.triggerAction`, so the helper used its DevTools-loaded popup fallback. This proves popup/runtime command plumbing, not audible Preview Voice, context-menu selected-text playback, or toolbar popup mechanics.

## Status update - 2026-06-23 22:59 -04:00
- **Now:** Local Windows packaging is functionally usable again: the packaged exe loads Torch/Kokoro, starts the API, opens `/control`, and passes packaged preview/speak/stop endpoint lifecycle smoke.
- **Next:** Finish macOS package visual/audio rows and remaining source/Tk/Chrome manual smoke rows, or record explicit accepted gaps.
- **Tests:** `.\build_windows.ps1` completed with Python 3.12.10; `.\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe -TimeoutSec 240 -IncludeAudio` passed executable launch, server ready, `/control`, `/preview status=playing`, `/speak status=playing`, `/stop status=stopped`, CORS origin matrix, and clean process stop.
- **Blockers:** Packaging validation now remains blocked by macOS menu-bar/tray, tray Open Control Panel, and macOS preview/speak/stop rows. Manual smoke remains blocked by source `/control` audible Preview/Speak, Tk audible Preview/Speak/Save/Stop, and Chrome extension Preview/context-menu selected-text playback rows.

### Windows Packaged Audio Lifecycle - Fixed
- **Done when:** The Windows packaged exe can synthesize and stop speech through the packaged API without crashing or relying on runtime downloads.
- **What changed:** Pinned Torch below the current frozen-runtime `c10.dll` regression, forced Windows PyInstaller builds to use `System32` VC runtime DLLs instead of stale JDK copies found on `PATH`, bundled Kokoro source files, bundled `en_core_web_sm` files and metadata, pinned the spaCy model wheel in `requirements.txt`, made `/status` report model-load failures as dependency issues, and tightened package/server smoke so `/preview` must return `status=playing`. Extended optional audio smoke to cover preview, stop, speak, and stop.
- **Evidence:** Before the fix, packaged `/preview` failed first on `torch\lib\c10.dll`, then on missing `kokoro\modules.py`, then on Misaki trying to run `spacy download` inside the frozen app. After the fix, `dist\ReadOut\_internal\msvcp140.dll` is version `14.50.35719.0` from `System32`, `dist\ReadOut\_internal\kokoro\modules.py` exists, `en_core_web_sm` package and dist-info exist, and the Windows package smoke with `-IncludeAudio` passed all rows.
- **Notes / risks:** This is packaged endpoint lifecycle evidence on Windows. It does not replace macOS tray/menu-bar visual checks or the separate manual source/Tk/Chrome smoke worksheet.

## Status update - 2026-06-23 23:22 -04:00
- **Now:** Manual smoke validation passes with repeatable runtime evidence for source `/control`, Tk desktop, and Chrome extension workflows.
- **Next:** Finish the macOS package visual/audio rows in `PACKAGING_VALIDATION.md`, or record explicit accepted gaps.
- **Tests:** `.\tools\control_browser_action_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` passed rendered `/control` Preview, Speak, Save WAV, and Stop; `.\tools\tk_desktop_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` passed Tk open/config persistence plus Preview, Speak, Save WAV, and Stop; `.\tools\extension_runtime_smoke.ps1 -PythonExe .\.venv\Scripts\python.exe -TimeoutSec 180` passed popup OFFLINE/READY, popup Preview, service-worker context-menu selected-text read-aloud, and Stop; `.\tools\manual_smoke_check.ps1` passed all rows.
- **Blockers:** Packaging validation still remains blocked by macOS menu-bar/tray visibility, tray Open Control Panel, and macOS preview/speak/stop lifecycle rows.

### Manual Runtime Smoke - Cleared
- **Done when:** The source control panel, Tk desktop, and Chrome extension smoke worksheet has repeatable evidence for the release rows.
- **What changed:** `tools/control_browser_action_smoke.ps1` now clicks rendered Preview and Speak in addition to Save WAV and Stop. `tools/tk_desktop_runtime_smoke.ps1` now uses a main-thread callback queue for Tk worker completions, exercises Preview/Speak/Save/Stop, removes the generated WAV, and restores local files. `ui.py` now allows longer POST calls for local synthesis so first/cold Kokoro preview or save does not falsely fail at 10 seconds. `extension/background.js` now uses a named context-menu handler, and `tools/extension_runtime_smoke.ps1` invokes that handler inside the loaded service worker with selected text.
- **Evidence:** Browser action smoke observed `Preview playing.`, `Playing…`, `Saved to ...readout_1782270830.wav` at 231,644 bytes, and `Playback stopped.` Tk smoke observed `Desktop Preview Voice action PASS`, `Desktop Speak action PASS`, `Desktop Save WAV action PASS` with a 222,044-byte WAV, and `Desktop Stop action PASS`. Extension runtime smoke observed `Popup Preview action PASS`, `Context menu Read aloud action PASS` with `selected text sent; stop=stopped`, and `Popup Stop action PASS`.
- **Notes / risks:** This is automated playback lifecycle evidence. It is stronger than static wiring checks, but it is not a subjective human speaker-listening transcript. macOS packaged tray/menu-bar and packaged macOS audible lifecycle still require a macOS target or accepted gaps.

## Status update - 2026-06-23 23:42 -04:00
- **Now:** The macOS packaged smoke helper and package-smoke workflow can produce stronger audio lifecycle evidence on the next macOS target run.
- **Next:** Push this update, let the macOS package-smoke workflow run with `--include-audio`, then use the resulting artifact to update `PACKAGING_VALIDATION.md` if it passes. Tray icon visibility and tray `Open Control Panel` still require macOS target/manual evidence or accepted gaps.
- **Tests:** `C:\Program Files\Git\bin\bash.exe -n tools/mac_package_smoke.sh` passed; focused release docs/tool tests passed with `35 passed`; `.\tools\packaging_validation_check.ps1` still fails only the macOS P3-A1 worksheet rows; `.\tools\roadmap_audit.ps1` passes roadmap coverage, upstream graph, Python, eSpeak, Architect, and manual smoke, then fails only packaging validation.
- **Blockers:** P3-A1 is still not green until the updated macOS package-smoke run proves audio lifecycle and the tray/menu-bar rows are passed or accepted as gaps.

### macOS Packaged Audio Lifecycle Gate - Tightened
- **Done when:** A macOS target/package-smoke run can prove packaged preview, stop, speak, and stop lifecycle instead of only `/preview`.
- **What changed:** `tools/mac_package_smoke.sh --include-audio` now requires `/preview` to return `preview=true` and `status=playing`, then verifies `/stop`, `/speak status=playing`, and a final `/stop`. The package-smoke workflow now runs the macOS package smoke with `--include-audio`. `PACKAGING_VALIDATION.md`, `RELEASE_CHECKLIST.md`, `NEXT_EXECUTOR_PROMPT.md`, and `ROADMAP_STATUS.md` now point at the stricter command.
- **Evidence:** Local syntax and focused release docs/tool tests passed on Windows. The actual macOS app/audio result must come from the next macOS workflow or target run.
- **Notes / risks:** This does not prove the tray icon is visible and does not click the tray `Open Control Panel` menu item. Those remain manual/target rows unless explicitly accepted as gaps.

## Status update - 2026-06-23 23:52 -04:00
- **Now:** macOS packaged audio lifecycle is verified by hosted package-smoke evidence.
- **Next:** Finish only the macOS visible tray/menu rows in `PACKAGING_VALIDATION.md`, or record explicit accepted gaps for those two rows.
- **Tests:** GitHub Actions package-smoke run `28073664040` passed both jobs. macOS job `83113369649` built `dist/ReadOut.app`, ran `./tools/mac_package_smoke.sh --app dist/ReadOut.app --include-audio`, and uploaded artifact `7839652216` with digest `sha256:1dbbb42e4bcd81a5ff69fc3c067b8a38f0b2b2afe5ad7d2ab5138c3fab465cfa`.
- **Blockers:** Packaging validation still remains blocked by macOS menu-bar/tray visibility and tray `Open Control Panel` selection.

### macOS Packaged Audio Lifecycle - Verified
- **Done when:** The packaged macOS app can launch, serve `/control`, run preview, stop, speak, stop, reject a blocked origin, and quit cleanly.
- **Evidence:** macOS package smoke reported `Launch packaged app PASS`, `Server ready PASS`, `GET /control PASS`, `POST /preview PASS status=playing; preview=true`, `POST /stop after preview PASS status=stopped`, `POST /speak PASS status=playing`, `POST /stop after speak PASS status=stopped`, `Blocked origin PASS`, and `App quits cleanly PASS`.
- **Notes / risks:** This is hosted macOS runner endpoint/audio lifecycle evidence, not a human visual check of the menu-bar icon. The two remaining P3-A1 rows are visual tray/menu rows only.

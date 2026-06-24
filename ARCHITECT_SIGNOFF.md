# ReadOut Architect Sign-off Packet

Last updated: 2026-06-23 23:52 -04:00

Purpose: give the Architect one compact place to accept or revise the roadmap
decisions that are implemented but still waiting on owner sign-off.

## How to Use
1. Review the decision and evidence links for each item.
2. Check **Accept** or **Revise**.
3. If revising, write the requested change in the notes field.
4. Copy final decisions back into `DECISION_LOG.md`.
5. Run `.\tools\architect_signoff_check.ps1` (`tools/architect_signoff_check.ps1`); every required row must show `PASS`.

## Required Sign-offs

| ID | Decision / Gate | Evidence | Accept | Revise | Notes |
|---|---|---|---|---|---|
| P0-A4 | Confirm local-only threat model and Phase 0 assumptions. | `THREAT_MODEL.md`, `DECISION_LOG.md`, `MILESTONE_LOG.md`, Notion Architect sign-off page | [x] | [ ] | Architect page verdict: ACCEPTED; local-only threat model accepted. |
| P1-A2 | Remove Browser engine tab until a real browser/system TTS backend exists. | `DECISION_LOG.md`, `tests/test_ui_copy.py`, `tests/test_server_api.py`, Notion Architect sign-off | [x] | [ ] | Architect decision: DELETE. |
| P1-A4 | Remove Auto-read control until trigger behavior and safe defaults are specified. | `DECISION_LOG.md`, `tests/test_ui_copy.py`, Notion Architect sign-off | [x] | [ ] | Architect decision: remove now; re-spec later as opt-in/off by default. |
| P1-A5 | Remove queue download buttons until queue items can produce deterministic WAV downloads. | `DECISION_LOG.md`, `tests/test_ui_copy.py`, Notion Architect sign-off | [x] | [ ] | Architect decision: DELETE. |
| P2-A1 | Make `/control` the official primary macOS UI; keep Tk as `READOUT_FORCE_TK=1` troubleshooting override. | `DECISION_LOG.md`, `README.md`, `tests/test_main_runtime.py`, `tests/test_server_api.py`, Notion Architect sign-off | [x] | [ ] | Architect direction accepted: `/control` is canonical; Tk remains override/troubleshooting path in this repo. |
| P2-A4 | Keep recent-read history local-only, off by default, capped, and clearable. | `DECISION_LOG.md`, `history_store.py`, `tests/test_history_store.py`, `tests/test_server_api.py`, Notion Architect sign-off | [x] | [ ] | Architect privacy contract accepted. |
| P3-A4 | Accept `RELEASE_CHECKLIST.md` as the required release gate. | `RELEASE_CHECKLIST.md`, `ROADMAP_STATUS.md`, `tests/test_release_docs.py`, Notion Architect sign-off | [x] | [ ] | Architect accepted checklist as reusable release gate; release still blocked until packaging/manual evidence rows are complete or accepted gaps. |

## Current Non-Architect Blockers
- Upstream graph reconciliation is cleared in the `roadmap-integration` worktree; `ROADMAP_STATUS.md` and `UPSTREAM_RECONCILIATION.md` now track the clean-branch state. The original dirty local `main` worktree remains a safety copy and should not be blindly pulled, merged, reset, or overwritten.
- Fresh source-only live checks passed on 2026-06-23 14:48 -04:00: temporary Uvicorn server, `tools/server_smoke.ps1` non-audio API/control smoke, and `tools/cors_origin_matrix.ps1` CORS matrix. These checks do not replace target package smoke, audible preview, Tk desktop, Chrome extension, or Architect acceptance.
- Hosted package-smoke run `28073664040` passed for Windows and macOS at commit `999cb7f`; `PACKAGING_VALIDATION.md` records package artifacts, macOS `/control`, macOS preview/stop/speak/stop audio lifecycle, macOS clean-quit evidence, and current Windows package evidence.
- P3-A1 still needs manual macOS menu-bar/tray visibility and tray `Open Control Panel` evidence, unless those gaps are explicitly accepted as release risks.
- P3-A2 Windows package validation is complete.
- Architect decision sign-off is now transcribed from the Notion Architect page. Manual smoke validation is complete with automated runtime evidence for source `/control`, Tk desktop, and Chrome extension workflows.

## Release Gate Rule
The Architect decision rows above are accepted. That does not make the release
green by itself: final release still requires `tools/packaging_validation_check.ps1`
and `tools/manual_smoke_check.ps1` to pass, or explicit accepted gaps for the
remaining target-specific visual/audio/manual rows.

Before final release, re-run `tools/release_preflight.ps1`, `tools/server_smoke.ps1`,
and `tools/cors_origin_matrix.ps1`, then confirm hosted package-smoke evidence
and target/manual worksheet evidence are still current.

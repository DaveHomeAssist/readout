# ReadOut Architect Sign-off Packet

Last updated: 2026-06-23 16:00 -04:00

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
| P0-A4 | Confirm local-only threat model and Phase 0 assumptions. | `THREAT_MODEL.md`, `DECISION_LOG.md`, `MILESTONE_LOG.md` | [ ] | [ ] | |
| P1-A2 | Remove Browser engine tab until a real browser/system TTS backend exists. | `DECISION_LOG.md`, `tests/test_ui_copy.py`, `tests/test_server_api.py` | [ ] | [ ] | |
| P1-A4 | Remove Auto-read control until trigger behavior and safe defaults are specified. | `DECISION_LOG.md`, `tests/test_ui_copy.py` | [ ] | [ ] | |
| P1-A5 | Remove queue download buttons until queue items can produce deterministic WAV downloads. | `DECISION_LOG.md`, `tests/test_ui_copy.py` | [ ] | [ ] | |
| P2-A1 | Make `/control` the official primary macOS UI; keep Tk as `READOUT_FORCE_TK=1` troubleshooting override. | `DECISION_LOG.md`, `README.md`, `tests/test_main_runtime.py`, `tests/test_server_api.py` | [ ] | [ ] | |
| P2-A4 | Keep recent-read history local-only, off by default, capped, and clearable. | `DECISION_LOG.md`, `history_store.py`, `tests/test_history_store.py`, `tests/test_server_api.py` | [ ] | [ ] | |
| P3-A4 | Accept `RELEASE_CHECKLIST.md` as the required release gate. | `RELEASE_CHECKLIST.md`, `ROADMAP_STATUS.md`, `tests/test_release_docs.py` | [ ] | [ ] | |

## Current Non-Architect Blockers
- Upstream graph reconciliation is cleared in the `roadmap-integration` worktree; `ROADMAP_STATUS.md` and `UPSTREAM_RECONCILIATION.md` now track the clean-branch state. The original dirty local `main` worktree remains a safety copy and should not be blindly pulled, merged, reset, or overwritten.
- Fresh source-only live checks passed on 2026-06-23 14:48 -04:00: temporary Uvicorn server, `tools/server_smoke.ps1` non-audio API/control smoke, and `tools/cors_origin_matrix.ps1` CORS matrix. These checks do not replace target package smoke, audible preview, Tk desktop, Chrome extension, or Architect acceptance.
- Hosted package-smoke run `28051156266` passed for Windows and macOS at `b2f02cee11ff6340ad5fcec51db4bb29e2856fdc`; `PACKAGING_VALIDATION.md` records the package artifacts and non-audio smoke evidence.
- P3-A1 still needs manual macOS menu-bar/tray visibility, tray `Open Control Panel`, audible preview/speak/stop lifecycle, and clean-quit evidence, unless those gaps are explicitly accepted as release risks.
- P3-A2 still needs manual Windows audible preview/speak/stop lifecycle evidence, unless that gap is explicitly accepted as a release risk.
- Manual smoke tests still remain for source `/control`, Tk desktop, Chrome extension popup, and audible playback workflows.

## Suggested Sign-off Rule
Do not accept P0-A4 or P3-A4 until upstream has been reconciled, `tools/release_preflight.ps1`, `tools/server_smoke.ps1`, `tools/cors_origin_matrix.ps1`, hosted package-smoke evidence, and the remaining manual smoke worksheets have been reviewed, or the target-specific gaps are explicitly accepted as release risks.

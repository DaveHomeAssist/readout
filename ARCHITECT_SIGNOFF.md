# ReadOut Architect Sign-off Packet

Last updated: 2026-06-23 06:33 -04:00

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
- Local `main` is still behind `origin/main` by 10 commits at the Git graph level. Engine registry, unified voice catalogue consumption, startup-race hardening, extension least privilege, docs/OpenAPI disabling, config-file permission hardening, and loopback Host guard have been ported locally. Remaining upstream UI/spec/packaging deltas still need review without weakening the exact-origin CORS allowlist or dropping preview/history/dependency/release-gate artifacts.
- P3-A1 still needs macOS PyInstaller build and tray/control-panel lifecycle validation on macOS.
- P3-A2 still needs a Windows target with Python 3.10-3.12 and `espeak-ng` installed, then `ReadOut.exe` build and server lifecycle validation.
- Manual smoke tests still remain for Tk desktop, Chrome extension popup, audio preview, packaged macOS lifecycle, and packaged Windows lifecycle.

## Suggested Sign-off Rule
Do not accept P0-A4 or P3-A4 until upstream has been reconciled, `tools/release_preflight.ps1`, `tools/server_smoke.ps1`, `tools/cors_origin_matrix.ps1`, and the relevant packaged-app smoke helper have been run on the intended release target, or the target-specific gaps are explicitly accepted as release risks.

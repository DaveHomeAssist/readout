# ReadOut Upstream Reconciliation

Last updated: 2026-06-23 13:30 -04:00

This file tracks how the roadmap work was reconciled onto a clean worktree
based on `origin/main`. It is a review aid, not permission to merge or
overwrite local roadmap work.

## Current Graph State

| Branch | State |
|---|---|
| Integration worktree | Branch `roadmap-integration`, based on `origin/main` |
| Upstream graph | `ahead=0; behind=0` before local roadmap edits |
| Release gate | Upstream graph blocker is cleared in this worktree; packaging/sign-off/manual smoke gates remain |

Do not run a blind pull, merge, rebase, checkout, or reset in the original
dirty roadmap worktree. This integration worktree exists so the reviewed
roadmap deltas can be validated without disturbing that local state.

## Upstream Commit Review

| Upstream commit | Subject | Local disposition |
|---|---|---|
| `a4bc0a2` | Keep canonical TTS desktop UI mockup | Present from upstream |
| `c7481b3` | Harden local API surface and startup race | Present from upstream, then tightened to exact-origin CORS |
| `afa1087` | Add feature specification | Present from upstream, then updated for roadmap behavior |
| `d7e1393` | Redesign control panel into canonical desktop GUI | Present from upstream, with preview/history/dependency additions preserved |
| `8f327b4` | Merge security implementation with control-panel redesign | Present from upstream, then tightened for roadmap security assumptions |
| `c5db9ed` | Retire Tk desktop UI | Partially superseded; roadmap makes `/control` primary on macOS but still keeps Tk available for non-macOS/troubleshooting |
| `bce6416` | Add pluggable engine layer and registry | Present from upstream |
| `422b635` | Wire control panel and extension to unified `/voices` catalogue | Present from upstream, with roadmap preview/history additions preserved |
| `8abc0ae` | Record pluggable engine layer and unified voice catalogue | Present from upstream, then updated by roadmap docs |
| `c158728` | Remove legacy browser engine controls; reject unsupported engines | Present from upstream |

## Local Decisions Preserved

- Exact browser origins are required through `allowed_origins` or `READOUT_ALLOWED_ORIGINS`; broad `chrome-extension://...` origin acceptance is not accepted for this roadmap.
- `/config` responses redact provider keys.
- `/preview` is request-local and must not mutate config, save audio, or add history.
- Recent-read history is off by default, stored locally when enabled, capped, and clearable.
- macOS packaged flow forces tray plus `/control`; Tk is not launched in the packaged macOS path.
- Tk remains available outside packaged macOS until Architect accepts full retirement.

## Review Commands

Run these from the repo root:

```powershell
.\tools\upstream_reconciliation.ps1
git log --oneline --decorate --left-right HEAD...origin/main
git diff --name-status HEAD..origin/main
```

## Remaining Release Risk

- The Git graph is reconciled in this integration worktree; the original dirty
  local `main` worktree remains a separate safety copy and should not be pulled
  over blindly.
- Target packaging validation remains separate: macOS requires a macOS build host; Windows requires Python 3.10-3.12, `espeak-ng`, and a built `dist\ReadOut\ReadOut.exe`.

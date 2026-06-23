# Project Instructions

## Project Purpose
ReadOut is a local-first desktop text-to-speech app for Dave's workstation workflows. It runs a FastAPI server on loopback port 7778, supports local Kokoro playback by default, and can be controlled by a browser extension or local control panel.

## Commands
| Task | Command |
|---|---|
| Install runtime deps | `python -m pip install -r requirements.txt` |
| Install test deps | `python -m pip install -r requirements-dev.txt` |
| Run dev | `python main.py --headless --no-browser` |
| Test | `python -m pytest` |
| Lint | TBD |
| Build macOS | `./build_mac.sh` |
| Build Windows | `.\build_windows.ps1` |
| Deploy | TBD |

## Conventions
- Follow existing Python style and keep changes small.
- Do not add dependencies without clear justification.
- Preserve the local Kokoro engine and port 7778 defaults.
- Do not echo API keys, secrets, or sensitive config values in HTTP responses, logs, tests, or docs.
- Treat browser-facing local endpoints as security-sensitive, even though the server is loopback-only.
- Keep CORS and Origin handling explicit. Do not reintroduce wildcard origins or regexes that allow every Chrome extension.

## Verification Required
Before final response, run the most relevant available checks:
1. `python -m pytest`
2. Manual smoke test for changed endpoints if a running server is practical
3. Build only when packaging files or runtime startup behavior changed

## Production Notes
- Phase 0 security stabilization ships before UI polish.
- Flag any risk to playback reliability, extension connectivity, local privacy, API key handling, or drive-by browser access.
- For CORS changes, provide an allowed/disallowed origin proof matrix.
- For risky changes, include rollback guidance.

## Architect / Executor Workflow
- Architect owns threat model, decision log, and acceptance gates.
- Codex owns implementation, refactors, tests, and packaging mechanics.
- For each `P#-A#`, restate the done condition, touch only the required modules, run tests, and record evidence in the milestone log.

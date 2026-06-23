# ReadOut Feature Specification

Status: current roadmap branch as-built notes
Date: 2026-06-23

ReadOut is a local-first desktop text-to-speech app. It runs a FastAPI server on
`127.0.0.1:7778`, serves a browser control panel at `/control`, and supports a
Chrome extension plus a tray/Tk desktop workflow.

## Core Surfaces
- `/control` browser control panel: speak, save WAV, stop, preview voice,
  update engine/voice/speed, toggle recent-read history, and clear history.
- Tk desktop UI: available on non-macOS and as a macOS troubleshooting override
  with `READOUT_FORCE_TK=1`; it loads the same `/voices` engine catalogue as
  the web control panel and extension, with static fallbacks for startup/offline
  conditions.
- Chrome extension: reads selected text, previews the selected voice, stops
  playback, and displays status/error/next-action text.
- Tray menu: starts the local server, opens `/control`, changes voice/engine,
  stops audio, and quits the process.

## Engines
The engine registry lives under `engines/`.

| Engine | ID | Data path | Auth | Notes |
|---|---|---|---|---|
| Kokoro | `kokoro` | Local | None | Default; supports voice blending. |
| OpenAI TTS | `openai` | Cloud | `openai_api_key` | Optional fallback; returns WAV for reliable decoding. |
| ElevenLabs | `elevenlabs` | Cloud | `elevenlabs_api_key` | Optional fallback; stream decode depends on local libsndfile MPEG support. |

`GET /voices` returns the backward-compatible Kokoro `voices` list and a unified
`engines` catalogue with per-engine voices and capability metadata. `/control`
and the extension popup consume that catalogue with local static fallbacks.

## Security And Privacy
- Browser `Origin` headers are rejected unless they exactly match a trusted
  local/default origin or `allowed_origins` / `READOUT_ALLOWED_ORIGINS`.
- Unknown browser origins receive `403` before endpoint side effects.
- FastAPI docs/OpenAPI routes are disabled.
- Non-loopback `Host` headers are rejected by `TrustedHostMiddleware`.
- `/config` redacts `openai_api_key` and `elevenlabs_api_key` in responses.
- Config directory/file permissions are hardened best-effort to `0700`/`0600`.
- Recent-read history is off by default, local-only, capped, and clearable.

## Key Endpoints
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Redirect to `/control`. |
| `GET` | `/control` | Browser control panel. |
| `POST` | `/speak` | Speak text using the configured engine. |
| `POST` | `/preview` | Play a short preview without saving or mutating config. |
| `POST` | `/stop` | Stop active playback. |
| `GET` | `/status` | Health, active config, dependency issues, model state. |
| `GET` | `/voices` | Kokoro voices plus unified engine catalogue. |
| `GET` | `/history` | Recent reads when enabled. |
| `DELETE` | `/history` | Clear recent-read history. |
| `PATCH` | `/config` | Persist allowed settings. |

## Packaging Gates
- Windows and macOS builds require Python 3.10-3.12 and `espeak-ng`.
- `tools/release_preflight.ps1` checks required artifacts, PowerShell syntax,
  upstream currency, Python/espeak prerequisites, secret scan, and optional live
  checks.
- `PACKAGING_VALIDATION.md` captures target macOS and Windows build/smoke
  evidence.

## Known Release Blockers
- Architect sign-off is still required in `ARCHITECT_SIGNOFF.md`.
- The integration worktree is based on `origin/main`; rerun
  `tools/upstream_reconciliation.ps1` before release to confirm no upstream
  graph drift was introduced.
- macOS packaged lifecycle validation requires a macOS target.
- Windows packaged lifecycle validation requires Python 3.10-3.12, `espeak-ng`,
  a built `dist\ReadOut\ReadOut.exe`, and package smoke results.

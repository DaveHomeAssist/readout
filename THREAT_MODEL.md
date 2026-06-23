# ReadOut Local-Only Threat Model

## Scope
ReadOut runs a loopback FastAPI service on `127.0.0.1:7778`, a browser control panel at `/control`, a Chrome extension, optional Tk desktop UI on non-macOS, and local TTS/audio code. Kokoro is local-only; OpenAI and ElevenLabs are external engines only when explicitly selected.

## Assets
- User text sent to `/speak` or stored in optional recent-read history.
- Provider API keys in `~/.readout/config.json`.
- Local playback control and saved WAV files.
- ReadOut config, history, and model-ready files under `~/.readout`.

## Actors
- Dave using local UI, extension, curl, or scripts.
- Trusted local browser clients explicitly allowed by origin.
- Untrusted remote websites visited in a browser.
- Other local processes running as the same OS user.
- External TTS providers when OpenAI or ElevenLabs is selected.

## Trust Boundaries
- Browser origin boundary: remote websites must not drive local endpoints.
- Local OS user boundary: same-user local processes and no-Origin curl/scripts are trusted for Phase 0.
- External provider boundary: text leaves the machine only for OpenAI/ElevenLabs engines.
- Local storage boundary: history is off by default; when enabled, history is plaintext local storage.

## Controls
- Origin guard rejects untrusted browser origins before endpoint side effects.
- Extension origins must be exact allowlist entries; wildcard origins are ignored.
- `/config` redacts provider API keys from HTTP responses.
- `/preview` does not save audio and does not mutate config.
- Recent-read history is local-only, off by default, capped, and clearable.
- Dependency issues are surfaced before first-run model failures.

## Explicit Assumptions
- ReadOut is not exposed on a LAN or public interface.
- Same-user local scripts are allowed to control ReadOut.
- Local filesystem access to `~/.readout` is outside the app's protection boundary.
- The Chrome extension ID is copied into `allowed_origins` after install.
- Provider API keys are already trusted to be present on disk when external engines are used.

## Residual Risks
- A malicious same-user local process can still call the loopback API.
- API keys remain plaintext on disk for provider SDK use.
- Recent-read history stores read text in plaintext when enabled.
- Shared-secret request authentication is not implemented yet.

## Architect Sign-off
- **Status:** Pending Architect review.
- **Decision needed:** Confirm Phase 0 local-only assumptions, especially whether same-user no-Origin callers remain trusted or require a shared-secret header in a later phase.

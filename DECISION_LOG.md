# ReadOut Decision Log

## 2026-06-21 - Phase 1 UI Truthfulness Cleanup

### P1-A2 - Browser Engine Tab
- **Decision:** Remove the desktop Browser engine tab until a real browser/system TTS backend is designed and testable.
- **Reason:** The backend only supports `kokoro`, `openai`, and `elevenlabs`. Keeping a Browser tab implied a functional engine that did not exist and could persist an unsupported config value.
- **Verification:** Desktop UI exposes only supported engines; `PATCH /config` rejects unsupported `engine` values.
- **Revisit when:** A browser/system voice implementation has a defined API path and acceptance tests.

### P1-A4 - Auto-read
- **Decision:** Remove the desktop Auto-read button for now.
- **Reason:** The control only toggled button color and did not trigger a defined, safe auto-read workflow.
- **Verification:** No visible Auto-read control remains in the desktop UI source.
- **Revisit when:** Safe defaults, clear state, and trigger behavior are specified.

### P1-A5 - Queue Download Buttons
- **Decision:** Remove queue-row download buttons for now.
- **Reason:** The buttons had no command and did not produce deterministic per-item downloads.
- **Verification:** Queue rows no longer render a download button.
- **Revisit when:** Queue items track the saved output path or can deterministically regenerate a WAV.

## 2026-06-21 - Phase 2 Control Surface Decisions

### P2-A1 - macOS Primary UI
- **Decision:** Make `/control` the official primary macOS UI. Keep the Tk desktop UI as a troubleshooting override via `READOUT_FORCE_TK=1`.
- **Reason:** The packaged macOS app already runs tray + browser control panel, and Tk has been unstable on newer macOS/Homebrew combinations.
- **Verification:** Runtime routing disables Tk on macOS by default, docs describe `/control` as primary, and `/control` exposes speak, save, stop, config, preview, and history controls.
- **Revisit when:** Tk runtime stability is proven across target macOS/Python builds.

### P2-A4 - Recent Reads History and Privacy
- **Decision:** Recent-read history is local-only, off by default, capped by `history_limit`, and clearable from `/control` or `DELETE /history`.
- **Reason:** Read text can be client-sensitive. Defaulting off avoids retaining client-facing content unless Dave explicitly enables it for convenience.
- **Verification:** `history_enabled` defaults to false; reads are only stored when enabled; `/control` shows an on/off checkbox and Clear History button; tests cover disabled, enabled, capped, and cleared history behavior.
- **Revisit when:** A different retention model is needed for release packaging or multi-device workflows.

## 2026-06-21 - Security and Release Gates

### P0-A4 - Local-only Threat Model
- **Decision:** Local-only threat model accepted by Architect in Notion `ARCH | ReadOut Architect Sign-off - Phase 0-3` and transcribed to `ARCHITECT_SIGNOFF.md`.
- **Reason:** The hardening work depends on explicit assumptions around loopback-only access, trusted no-Origin local callers, external TTS providers, and local plaintext storage.
- **Verification:** Threat-model doc includes actors, assets, trust boundaries, controls, explicit assumptions, residual risks, and sign-off status; `tools/architect_signoff_check.ps1` verifies the local transcribed gate.
- **Revisit when:** A shared-secret header, LAN binding, or new storage/sync behavior is introduced.

### P3-A4 - Release Checklist
- **Decision:** Use `RELEASE_CHECKLIST.md` for every release candidate; Architect accepted this as the reusable release gate in Notion `ARCH | ReadOut Architect Sign-off - Phase 0-3`, and the decision is transcribed to `ARCHITECT_SIGNOFF.md`.
- **Reason:** Releases need one repeatable checklist with security, test, smoke, packaging, and release-note gates.
- **Verification:** Checklist includes security gate, full test suite, CORS/redaction checks, macOS build gate, Windows build gate, and milestone evidence requirements; `tools/architect_signoff_check.ps1` verifies the accepted local gate. Packaging/manual evidence still remains separate release evidence.
- **Revisit when:** Packaging or distribution process changes.

# ReadOut — Manual QA Checklist

Automated tests cover the HTTP contract, config logic, CORS policy, and engine
dispatch (see [Testing](../CLAUDE.md#testing)). They deliberately stub the
parts that need a human or real hardware. This checklist covers **only those
parts**: real audio, the model download, engine switching with live keys, and
the Chrome extension.

Run these on a real dev machine against a real daemon (`python main.py`), not
in CI. The `scripts/qa_probe.py` driver talks to the running daemon for you.

---

## 0. Pre-flight

- [ ] `pip install -r requirements.txt` (full runtime stack incl. kokoro/torch)
- [ ] `brew install espeak-ng` (macOS) — required by Kokoro
- [ ] Start the daemon: `python main.py`
- [ ] In another shell: `python scripts/qa_probe.py status` → `HTTP 200`, `"status"` is `loading` or `ready`

## 1. First-run model download (Kokoro)

- [ ] On a machine with no `~/.readout/.model_ready`, start the daemon
- [ ] `qa_probe.py status` reports `"status": "loading"` and `"model_ready": false` initially
- [ ] After the ~300 MB download + load, status flips to `"ready"` / `"model_ready": true`
- [ ] `~/.readout/.model_ready` now exists; a restart comes up `ready` immediately

## 2. Real audio playback (Kokoro)

- [ ] `qa_probe.py speak "Hello from ReadOut"` → audio plays through the default output
- [ ] `--voice af_sky` / `--voice am_adam` audibly change the voice
- [ ] `--speed 1.5` is faster, `--speed 0.75` slower
- [ ] While audio is playing, `qa_probe.py stop` (or a new `speak`) halts it promptly

## 3. File save

- [ ] `qa_probe.py speak "save test" --save` → response has `saved_to`; a `.wav` exists there
- [ ] Set `always_save` (`qa_probe.py config` is keys-only; edit `~/.readout/config.json` or use the control panel) → every `speak` writes a file
- [ ] Default save dir is `~/Desktop/ReadOut` unless `save_dir` is overridden

## 4. Engine switching (OpenAI / ElevenLabs) — needs live keys

- [ ] `qa_probe.py config --engine openai --openai-key sk-...` → `HTTP 200`, response shows `"openai_api_key": "***"` (redacted) and the command prints no warning
- [ ] `~/.readout/config.json` contains the **real** key (redaction is response-only)
- [ ] `qa_probe.py speak "openai voice test" --voice nova` → OpenAI audio plays; `stop` halts it
- [ ] Switch to `--engine elevenlabs --elevenlabs-key ...`; `speak` plays ElevenLabs audio
      - Note: ElevenLabs streams MP3; if playback fails with a decode error, the
        local `soundfile`/`libsndfile` build lacks MP3 support (needs ≥ 1.1) — see issue 003 context
- [ ] A bad key surfaces a clean `{"status":"error","message":"... 401 ..."}`, not a stack trace
- [ ] Switch back: `qa_probe.py config --engine kokoro`

## 5. Control panel (served by the daemon)

- [ ] Open `http://127.0.0.1:7778/` → redirects to `/control`, panel renders
- [ ] The panel can change voice/speed/engine and trigger speak/stop
- [ ] The panel does **not** display stored API keys (the server never sends them back)

## 6. Chrome extension

- [ ] Load unpacked: `chrome://extensions` → Developer mode → Load unpacked → `extension/`
- [ ] Select text on any page → right-click → "Read aloud via ReadOut" → audio plays
- [ ] Toolbar popup: status indicator shows daemon up/down; Play/Stop work; settings persist
- [ ] With the daemon stopped, the popup shows an unreachable/error state (no crash)

## 7. Security smoke (the issue-002 regression)

- [ ] `python scripts/qa_probe.py cors --origin https://evil.com` → prints **BLOCKED** (exit 0)
- [ ] `... cors --origin chrome-extension://abcdefghijklmnopabcdefghijklmnop` → prints **ALLOWED**
- [ ] In a random website's DevTools console, `fetch('http://127.0.0.1:7778/status')` is blocked by CORS
- [ ] `qa_probe.py config --openai-key sk-canary` then confirm `sk-canary` never appears in the HTTP response (the driver warns loudly if it does)
- [ ] Known gap (issue 003): a cross-origin page **can** still fire `POST /stop` as a side effect — verify impact is limited to halting playback

## 8. Platform: macOS 26 Tk skip (issue 001)

- [ ] On macOS 26+, the daemon + tray run without launching the Tk window (no `GetRGBA`/NSApplication crash)
- [ ] On macOS < 26 / other platforms, the Tk window still appears as before

---

### Quick automated cross-checks (optional, not a substitute for the above)

```bash
scripts/smoke.sh                 # boots the real app in a subprocess, probes liveness + CORS
python -m pytest tests/e2e -v    # live-server harness over a real socket (audio stubbed)
python -m pytest -m "not e2e"    # fast in-process unit/integration suite only
```

# ReadOut — How to Use

## Quick Start

### 1. Start the desktop service
```bash
cd readout
source .venv/bin/activate
python main.py --headless --no-browser
```
A system tray icon (soundwave bars) appears in your menu bar. First launch downloads the Kokoro voice model (~300 MB) — one-time only.

If Homebrew Python crashes while opening the desktop window because it is linked
against Tk 9 on a newer macOS build, use the browser control panel. On macOS,
this is the primary UI:

```bash
python main.py --headless --no-browser
```

Then open the local control panel at `http://127.0.0.1:7778/control`.

### 2. Install the browser extension
1. Open Chrome → `chrome://extensions`
2. Toggle **Developer mode** (top-right)
3. Click **Load unpacked** → select the `extension/` folder
4. Copy the extension ID shown on the ReadOut card
5. Add the exact extension origin to `~/.readout/config.json`:
   ```json
   {
     "allowed_origins": ["chrome-extension://YOUR_EXTENSION_ID"]
   }
   ```
6. The ReadOut icon appears in your toolbar

### 3. Use it

**From any web page:**
- Select text → right-click → **"Read aloud"**
- A green toast confirms playback started
- Right-click anywhere → **"Stop reading"** to cancel

**From the extension popup:**
- Click the ReadOut icon in your Chrome toolbar
- It shows connection status, voice, engine, and speed controls
- Select text on a page, then click **"Read Selection"**

**From the desktop window:**
- Paste or type text in the text area
- Pick a voice and speed
- Hit the green play button

---

## Controls

### Voices
18 built-in Kokoro voices. Change via:
- The desktop UI voice dropdown
- The extension popup dropdown
- The system tray → Voice menu
- API: `PATCH http://localhost:7778/config` with `{"voice": "am_adam"}`

Use **Preview Voice** in the desktop UI, browser control panel, or extension popup to hear a short sample without entering read text.

### Speed
Drag the speed slider (0.5x to 2.0x). Default is 1.0x.

### Engine switching
ReadOut supports three TTS backends:
- **Kokoro** (default) — runs locally, no API key needed, no data leaves your machine
- **OpenAI TTS** — requires an API key in `~/.readout/config.json`
- **ElevenLabs** — requires an API key in `~/.readout/config.json`

Switch engines from the desktop UI tabs, the extension popup, or the tray menu.

### Saving audio
- Click **"Save WAV"** in the desktop UI to save current text as a WAV file
- Right-click selected text → **"Read aloud & save WAV"** from the extension
- Files save to `~/Desktop/ReadOut/` by default

### Recent reads and privacy
- Recent-read history is **off by default**
- Turn it on from `/control` with **Remember recent reads on this device**
- History is stored locally in `~/.readout/history.json`
- Use **Clear History** in `/control` or `DELETE /history` to delete it

---

## Config file

All settings live in `~/.readout/config.json`. Edits take effect immediately — no restart needed.

```json
{
  "voice": "af_heart",
  "speed": 1.0,
  "engine": "kokoro",
  "always_save": false,
  "save_dir": "~/Desktop/ReadOut",
  "port": 7778,
  "openai_api_key": "",
  "elevenlabs_api_key": "",
  "allowed_origins": [],
  "history_enabled": false,
  "history_limit": 20
}
```

`allowed_origins` is for trusted browser clients only. Local curl/scripts that
send no `Origin` header do not need to be listed.

---

## API (for scripts and automation)

The local server runs at `http://localhost:7778`.

```bash
# Speak text
curl -X POST http://localhost:7778/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_heart", "speed": 1.0}'

# Preview a voice
curl -X POST http://localhost:7778/preview \
  -H "Content-Type: application/json" \
  -d '{"voice": "af_heart", "speed": 1.0}'

# Stop playback
curl -X POST http://localhost:7778/stop

# Check status
curl http://localhost:7778/status

# List voices
curl http://localhost:7778/voices

# Recent reads, only populated when enabled
curl http://localhost:7778/history

# Clear recent reads
curl -X DELETE http://localhost:7778/history

# Change settings
curl -X PATCH http://localhost:7778/config \
  -H "Content-Type: application/json" \
  -d '{"voice": "am_adam", "speed": 1.2}'
```

---

## Troubleshooting

**Dependency warning in the popup/control panel:**
- Python must be 3.10-3.12
- Install app packages with `python -m pip install -r requirements.txt`
- Install `espeak-ng` and confirm `espeak-ng --version` works

**Extension context menu does nothing:**
- Make sure the desktop app is running (`python main.py`)
- Confirm `~/.readout/config.json` includes your exact `chrome-extension://...` origin
- Reload the page you're trying to use it on (content script needs to load)
- Check `chrome://extensions` for errors on the ReadOut card
- Won't work on `chrome://` or `edge://` system pages

**No audio plays:**
- Check your system audio output is set correctly
- On macOS: `brew install espeak-ng` if you haven't already
- Check the tray icon — orange dot means the model is still loading

**Port conflict:**
- ReadOut uses port 7778 by default (7777 is reserved for DaveLLM)
- Change in `~/.readout/config.json` AND in `extension/background.js` + `extension/popup.js`

**Python version:**
- Kokoro requires Python 3.10–3.12.
- macOS/Linux: check with `.venv/bin/python --version` or `python3.12 --version`.
- Windows: check with `py -3.12 --version`, `py -3.11 --version`, or `py -3.10 --version`.

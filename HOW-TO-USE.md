# ReadOut — How to Use

## Quick Start

### 1. Start the desktop service
```bash
cd readout
source .venv/bin/activate
python main.py
```
A system tray icon (soundwave bars) appears in your menu bar. First launch downloads the Kokoro voice model (~300 MB) — one-time only.

For API-only development without the tray or auto-opened control panel:

```bash
python main.py --headless --no-browser
```

Then open the local control panel at `http://127.0.0.1:7778/control`.

### 2. Install the browser extension
1. Open Chrome → `chrome://extensions`
2. Toggle **Developer mode** (top-right)
3. Click **Load unpacked** → select the `extension/` folder
4. The ReadOut icon appears in your toolbar

### 3. Use it

**From any web page:**
- Select text → right-click → **"Read aloud"**
- A green toast confirms playback started
- Right-click anywhere → **"Stop reading"** to cancel

**From the extension popup:**
- Click the ReadOut icon in your Chrome toolbar
- It shows connection status, voice, engine, and speed controls
- Select text on a page, then click **"Read Selection"**

**From the local control panel:**
- Paste or type text in the text area
- Pick a voice and speed
- Click **Speak**

---

## Controls

### Voices
18 built-in Kokoro voices. Change via:
- The control panel voice dropdown
- The extension popup dropdown
- The system tray → Voice menu
- API: `PATCH http://localhost:7778/config` with `{"voice": "am_adam"}`

### Speed
Drag the speed slider (0.5x to 2.0x). Default is 1.0x.

### Engine switching
ReadOut supports three TTS backends:
- **Kokoro** (default) — runs locally, no API key needed, no data leaves your machine
- **OpenAI TTS** — requires an API key in `~/.readout/config.json`
- **ElevenLabs** — requires an API key in `~/.readout/config.json`

Switch engines from the control panel, the extension popup, or the tray menu.

### Saving audio
- Click **"Speak & Save WAV"** in the control panel to save current text as a WAV file
- Right-click selected text → **"Read aloud & save WAV"** from the extension
- Files save to `~/Desktop/ReadOut/` by default

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
  "elevenlabs_api_key": ""
}
```

---

## API (for scripts and automation)

The local server runs at `http://localhost:7778`.

```bash
# Speak text
curl -X POST http://localhost:7778/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_heart", "speed": 1.0}'

# Stop playback
curl -X POST http://localhost:7778/stop

# Check status
curl http://localhost:7778/status

# List voices
curl http://localhost:7778/voices

# Change settings
curl -X PATCH http://localhost:7778/config \
  -H "Content-Type: application/json" \
  -d '{"voice": "am_adam", "speed": 1.2}'
```

---

## Troubleshooting

**Extension context menu does nothing:**
- Make sure the desktop app is running (`python main.py`)
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
- Kokoro requires Python 3.10–3.12. Check with `.venv/bin/python3 --version`

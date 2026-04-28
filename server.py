"""
server.py — ReadOut REST API
Endpoints:  POST /speak   POST /stop   GET /status   GET /voices   PATCH /config
CORS open to localhost — browser extension hits this directly.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

import tts_engine
import config as cfg_module

app = FastAPI(title="ReadOut TTS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to chrome-extension://... in production
    allow_methods=["*"],
    allow_headers=["*"],
)


CONTROL_PANEL_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReadOut Control Panel</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e0e0e;
      --panel: #161616;
      --panel-2: #1e1e1e;
      --panel-3: #262626;
      --border: #2a2a2a;
      --text: #e8e8e8;
      --muted: #8b8b8b;
      --accent: #b8f542;
      --danger: #ff5252;
      --warn: #ffaa52;
      --blue: #52a8ff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at top, rgba(184, 245, 66, 0.08), transparent 28%),
        linear-gradient(180deg, #111 0%, #090909 100%);
      color: var(--text);
      font-family: "SF Mono", "IBM Plex Mono", "Courier New", monospace;
    }
    .shell {
      width: min(760px, calc(100vw - 24px));
      margin: 24px auto;
      padding: 20px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(22, 22, 22, 0.94);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
    }
    .topbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
    }
    .title {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: var(--panel-2);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .status[data-state="ready"] { color: var(--accent); }
    .status[data-state="loading"] { color: var(--warn); }
    .status[data-state="offline"] { color: var(--danger); }
    .note {
      margin-bottom: 16px;
      padding: 12px 14px;
      border: 1px solid rgba(82, 168, 255, 0.3);
      border-radius: 12px;
      background: rgba(82, 168, 255, 0.08);
      color: #cfe5ff;
      font-size: 13px;
      line-height: 1.5;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .field.wide { grid-column: 1 / -1; }
    label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    select, textarea, input[type="range"] {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--panel-2);
      color: var(--text);
      padding: 12px 14px;
      font: inherit;
    }
    textarea {
      min-height: 220px;
      resize: vertical;
      line-height: 1.55;
    }
    .speed-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .speed-value {
      min-width: 48px;
      text-align: right;
      color: var(--accent);
      font-size: 14px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }
    button {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
      font: inherit;
      color: var(--text);
      background: var(--panel-2);
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #091100;
      font-weight: 700;
    }
    button.stop {
      border-color: rgba(255, 82, 82, 0.5);
      color: var(--danger);
    }
    .meta {
      margin-top: 16px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    @media (max-width: 640px) {
      .shell { margin: 12px auto; padding: 16px; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div class="title">ReadOut Control Panel</div>
      <div id="status" class="status" data-state="offline">Offline</div>
    </div>
    <div class="note">
      This browser control panel is the fallback for systems where the desktop Tk window cannot start.
      The local API stays at <code>http://127.0.0.1:7778</code> unless you changed the configured port.
    </div>
    <section class="grid">
      <div class="field">
        <label for="engine">Engine</label>
        <select id="engine">
          <option value="kokoro">Kokoro (local)</option>
          <option value="openai">OpenAI TTS</option>
          <option value="elevenlabs">ElevenLabs</option>
        </select>
      </div>
      <div class="field">
        <label for="voice">Voice</label>
        <select id="voice"></select>
      </div>
      <div class="field wide">
        <label for="text">Text</label>
        <textarea id="text" placeholder="Paste text here, then click Speak."></textarea>
      </div>
      <div class="field wide">
        <label for="speed">Speed</label>
        <div class="speed-row">
          <input id="speed" type="range" min="0.5" max="2.0" step="0.1" value="1.0">
          <div id="speedValue" class="speed-value">1.0x</div>
        </div>
      </div>
    </section>
    <div class="actions">
      <button id="speakBtn" class="primary" type="button">Speak</button>
      <button id="saveBtn" type="button">Speak + Save WAV</button>
      <button id="stopBtn" class="stop" type="button">Stop</button>
      <button id="refreshBtn" type="button">Refresh Status</button>
    </div>
    <div class="meta" id="meta">
      Waiting for local server status.
    </div>
  </main>
  <script>
    const BASE = window.location.origin;
    const VOICES = {
      kokoro: [
        "af_heart", "af_sky", "af_bella", "af_sarah", "af_nicole",
        "af_jessica", "af_nova", "af_river", "af_kore", "af_aoede",
        "am_adam", "am_echo", "am_michael", "am_fenrir",
        "bf_emma", "bf_isabella", "bm_george", "bm_lewis"
      ],
      openai: ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
      elevenlabs: ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"]
    };

    const els = {
      status: document.getElementById("status"),
      meta: document.getElementById("meta"),
      engine: document.getElementById("engine"),
      voice: document.getElementById("voice"),
      text: document.getElementById("text"),
      speed: document.getElementById("speed"),
      speedValue: document.getElementById("speedValue"),
      speakBtn: document.getElementById("speakBtn"),
      saveBtn: document.getElementById("saveBtn"),
      stopBtn: document.getElementById("stopBtn"),
      refreshBtn: document.getElementById("refreshBtn")
    };

    function updateVoices(engine, selectedVoice) {
      const options = (VOICES[engine] || []).map((voice) => {
        const selected = voice === selectedVoice ? " selected" : "";
        return `<option value="${voice}"${selected}>${voice}</option>`;
      });
      els.voice.innerHTML = options.join("");
      if (!els.voice.value && VOICES[engine]?.length) {
        els.voice.value = VOICES[engine][0];
      }
    }

    function setStatus(state, detail) {
      const label = state === "ready" ? "Ready" : state === "loading" ? "Loading" : "Offline";
      els.status.dataset.state = state;
      els.status.textContent = label;
      if (detail) {
        els.meta.textContent = detail;
      }
    }

    async function patchConfig(payload) {
      await fetch(`${BASE}/config`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    async function refreshStatus() {
      try {
        const response = await fetch(`${BASE}/status`, { signal: AbortSignal.timeout(2500) });
        const data = await response.json();
        setStatus(data.status || "offline", `Engine: ${data.engine || "unknown"} | Voice: ${data.voice || "unknown"} | Speed: ${data.speed || "1.0"}x`);
        els.engine.value = data.engine || "kokoro";
        updateVoices(els.engine.value, data.voice);
        els.speed.value = data.speed || 1.0;
        els.speedValue.textContent = `${Number(els.speed.value).toFixed(1)}x`;
      } catch (_error) {
        setStatus("offline", "The local ReadOut API is not responding yet.");
      }
    }

    async function speak(save) {
      const text = els.text.value.trim();
      if (!text) {
        els.meta.textContent = "Enter some text first.";
        return;
      }
      els.meta.textContent = save ? "Saving and speaking..." : "Speaking...";
      const response = await fetch(`${BASE}/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          voice: els.voice.value,
          speed: Number(els.speed.value),
          save
        })
      });
      const data = await response.json();
      els.meta.textContent = data.saved_to
        ? `Saved to ${data.saved_to}`
        : data.message || `Status: ${data.status}`;
      await refreshStatus();
    }

    els.engine.addEventListener("change", async () => {
      updateVoices(els.engine.value);
      await patchConfig({ engine: els.engine.value, voice: els.voice.value });
      await refreshStatus();
    });

    els.voice.addEventListener("change", async () => {
      await patchConfig({ voice: els.voice.value });
      await refreshStatus();
    });

    els.speed.addEventListener("input", () => {
      els.speedValue.textContent = `${Number(els.speed.value).toFixed(1)}x`;
    });

    els.speed.addEventListener("change", async () => {
      await patchConfig({ speed: Number(els.speed.value) });
      await refreshStatus();
    });

    els.speakBtn.addEventListener("click", () => speak(false));
    els.saveBtn.addEventListener("click", () => speak(true));
    els.stopBtn.addEventListener("click", async () => {
      await fetch(`${BASE}/stop`, { method: "POST" });
      els.meta.textContent = "Playback stopped.";
      await refreshStatus();
    });
    els.refreshBtn.addEventListener("click", refreshStatus);

    updateVoices("kokoro");
    refreshStatus();
  </script>
</body>
</html>
"""


# ── Request / response models ─────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text:  str
    voice: str   | None = None
    speed: float | None = None
    save:  bool         = False


class ConfigUpdate(BaseModel):
    voice:            str   | None = None
    speed:            float | None = None
    always_save:      bool  | None = None
    engine:           str   | None = None
    openai_api_key:   str   | None = None
    elevenlabs_api_key: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/control")


@app.get("/control", response_class=HTMLResponse, include_in_schema=False)
def control_panel():
    return HTMLResponse(CONTROL_PANEL_HTML)

@app.post("/speak")
def speak(req: SpeakRequest):
    """
    Synthesise and play text.
    Routes to the active engine from config.
    """
    cfg    = cfg_module.get_config()
    engine = cfg.get("engine", "kokoro")

    if engine == "openai":
        return _speak_openai(req, cfg)
    if engine == "elevenlabs":
        return _speak_elevenlabs(req, cfg)

    # Default: Kokoro local
    return tts_engine.speak(
        text  = req.text,
        voice = req.voice,
        speed = req.speed,
        save  = req.save,
    )


@app.post("/stop")
def stop():
    tts_engine.stop_audio()
    return {"status": "stopped"}


@app.get("/status")
def status():
    cfg = cfg_module.get_config()
    return {
        "status":        "loading" if tts_engine.is_loading() else "ready",
        "engine":        cfg.get("engine"),
        "voice":         cfg.get("voice"),
        "speed":         cfg.get("speed"),
        "model_ready":   not tts_engine.is_first_run(),
        "load_error":    tts_engine.get_load_error(),
        "version":       "1.0.0",
    }


@app.get("/voices")
def voices():
    return {"voices": tts_engine.list_voices_labeled()}


@app.patch("/config")
def update_config(update: ConfigUpdate):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    cfg_module.set_config(updates)
    return {"status": "updated", "config": cfg_module.get_config()}


# ── Engine fallbacks ──────────────────────────────────────────────────────────

def _speak_openai(req: SpeakRequest, cfg: dict) -> dict:
    try:
        import io
        import openai
        import sounddevice as sd
        import soundfile as sf

        client   = openai.OpenAI(api_key=cfg["openai_api_key"])
        response = client.audio.speech.create(
            model = "tts-1",
            voice = req.voice or "alloy",
            input = req.text,
            speed = req.speed or 1.0,
        )
        buf  = io.BytesIO(response.content)
        data, sr = sf.read(buf)
        sd.play(data, samplerate=sr)
        return {"status": "playing", "engine": "openai"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _speak_elevenlabs(req: SpeakRequest, cfg: dict) -> dict:
    try:
        import io
        import requests
        import sounddevice as sd
        import soundfile as sf

        vid     = req.voice or "21m00Tcm4TlvDq8ikWAM"   # Rachel default
        url     = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/stream"
        headers = {
            "xi-api-key":    cfg["elevenlabs_api_key"],
            "Content-Type":  "application/json",
        }
        r    = requests.post(
            url,
            json    = {"text": req.text, "model_id": "eleven_monolingual_v1"},
            headers = headers,
            timeout = 30,
        )
        buf  = io.BytesIO(r.content)
        data, sr = sf.read(buf)
        sd.play(data, samplerate=sr)
        return {"status": "playing", "engine": "elevenlabs"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

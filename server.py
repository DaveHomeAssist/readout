"""
server.py — ReadOut REST API
Endpoints:  POST /speak   POST /stop   GET /status   GET /voices   PATCH /config
CORS open to localhost — browser extension hits this directly.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

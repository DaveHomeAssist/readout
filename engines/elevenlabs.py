"""ElevenLabs — cloud engine (egress only when explicitly selected)."""
from __future__ import annotations

import tts_engine
from engines.base import TTSEngine

# Voice "ids" here are the human names the UI shows; the synth call passes the
# selected value straight through as the ElevenLabs voice id in the URL.
_VOICES = [
    {"id": "Rachel", "label": "Rachel"},
    {"id": "Domi",   "label": "Domi"},
    {"id": "Bella",  "label": "Bella"},
    {"id": "Antoni", "label": "Antoni"},
    {"id": "Elli",   "label": "Elli"},
    {"id": "Josh",   "label": "Josh"},
    {"id": "Arnold", "label": "Arnold"},
    {"id": "Adam",   "label": "Adam"},
    {"id": "Sam",    "label": "Sam"},
]


class ElevenLabsEngine(TTSEngine):
    name = "elevenlabs"
    label = "ElevenLabs"
    is_local = False
    requires_key = "elevenlabs_api_key"
    supports_blend = False

    def list_voices(self) -> list[dict]:
        return _VOICES

    def synthesize(self, req, cfg: dict) -> dict:
        try:
            import requests

            vid     = req.voice or "21m00Tcm4TlvDq8ikWAM"   # Rachel default
            url     = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/stream"
            headers = {
                "xi-api-key":   cfg["elevenlabs_api_key"],
                "Content-Type": "application/json",
            }
            r = requests.post(
                url,
                json    = {"text": req.text, "model_id": "eleven_monolingual_v1"},
                headers = headers,
                timeout = 30,
            )
            if not r.ok:
                # ElevenLabs returns a JSON error body on failure; surface it
                # instead of letting soundfile choke on non-audio bytes.
                return {"status": "error", "message": f"ElevenLabs API {r.status_code}: {r.text[:200]}"}

            # This endpoint streams MP3 by default and offers no WAV option (unlike
            # the OpenAI path's response_format="wav"), so decoding relies on a
            # soundfile/libsndfile build with MPEG support (libsndfile >= 1.1).
            data, sr = tts_engine.read_audio(r.content)
            tts_engine.play_audio(data, sr)
            result = {"status": "playing", "engine": "elevenlabs"}
            if req.save or cfg.get("always_save", False):
                result["saved_to"] = tts_engine.save_wav(data, sr)
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

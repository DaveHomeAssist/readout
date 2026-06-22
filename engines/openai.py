"""OpenAI TTS — cloud engine (egress only when explicitly selected)."""
from __future__ import annotations

import tts_engine
from engines.base import TTSEngine

_VOICES = [
    {"id": "alloy",   "label": "Alloy"},
    {"id": "echo",    "label": "Echo"},
    {"id": "fable",   "label": "Fable"},
    {"id": "onyx",    "label": "Onyx"},
    {"id": "nova",    "label": "Nova"},
    {"id": "shimmer", "label": "Shimmer"},
]


class OpenAIEngine(TTSEngine):
    name = "openai"
    label = "OpenAI TTS"
    is_local = False
    requires_key = "openai_api_key"
    supports_blend = False

    def list_voices(self) -> list[dict]:
        return _VOICES

    def synthesize(self, req, cfg: dict) -> dict:
        try:
            import openai

            client   = openai.OpenAI(api_key=cfg["openai_api_key"])
            response = client.audio.speech.create(
                model           = "tts-1",
                voice           = req.voice or "alloy",
                input           = req.text,
                speed           = req.speed or 1.0,
                response_format = "wav",   # WAV decodes reliably via soundfile
            )
            data, sr = tts_engine.read_audio(response.content)
            tts_engine.play_audio(data, sr)
            result = {"status": "playing", "engine": "openai"}
            if req.save or cfg.get("always_save", False):
                result["saved_to"] = tts_engine.save_wav(data, sr)
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

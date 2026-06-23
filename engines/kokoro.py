"""Kokoro local TTS engine."""
from __future__ import annotations

import tts_engine
from engines.base import TTSEngine


class KokoroEngine(TTSEngine):
    name = "kokoro"
    label = "Kokoro (local)"
    is_local = True
    requires_key = None
    supports_blend = True

    def list_voices(self) -> list[dict]:
        return tts_engine.list_voices_labeled()

    def synthesize(self, req, cfg: dict) -> dict:
        return tts_engine.speak(
            text=req.text,
            voice=req.voice,
            speed=req.speed,
            save=req.save,
            allow_always_save=getattr(req, "allow_always_save", True),
        )

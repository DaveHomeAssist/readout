"""Tests for the pluggable engine layer (engines/ package + registry).

The per-engine OpenAI/ElevenLabs synthesis paths are covered end-to-end in
test_engine_fallbacks.py (via the server shims that delegate here). These tests
lock in the registry, the capability metadata, and the catalogue shape that the
control panel + extension depend on.
"""
from __future__ import annotations

import types

import tts_engine
from engines import registry
from engines.kokoro import KokoroEngine
from engines.openai import OpenAIEngine
from engines.elevenlabs import ElevenLabsEngine


def test_registry_resolves_known_engines():
    assert isinstance(registry.get("kokoro"), KokoroEngine)
    assert isinstance(registry.get("openai"), OpenAIEngine)
    assert isinstance(registry.get("elevenlabs"), ElevenLabsEngine)
    assert set(registry.names()) == {"kokoro", "openai", "elevenlabs"}


def test_registry_unknown_falls_back_to_default():
    assert registry.get("nonsense").name == "kokoro"
    assert registry.get(None).name == "kokoro"


def test_catalogue_shape_and_capabilities():
    cat = {e["name"]: e for e in registry.catalogue()}
    assert set(cat) == {"kokoro", "openai", "elevenlabs"}
    for entry in cat.values():
        assert {"name", "label", "is_local", "requires_key",
                "supports_blend", "voices"} <= entry.keys()
        assert isinstance(entry["voices"], list) and entry["voices"]
        assert {"id", "label"} <= entry["voices"][0].keys()

    # Capability metadata drives the UI (key fields, blend hint, egress).
    assert cat["kokoro"]["is_local"] is True
    assert cat["kokoro"]["requires_key"] is None
    assert cat["kokoro"]["supports_blend"] is True
    assert cat["openai"]["is_local"] is False
    assert cat["openai"]["requires_key"] == "openai_api_key"
    assert cat["elevenlabs"]["is_local"] is False
    assert cat["elevenlabs"]["requires_key"] == "elevenlabs_api_key"


def test_kokoro_engine_delegates_to_tts_engine(monkeypatch):
    captured = {}

    def fake_speak(text, voice, speed, save):
        captured.update(text=text, voice=voice, speed=speed, save=save)
        return {"status": "playing", "voice": voice}

    monkeypatch.setattr(tts_engine, "speak", fake_speak)
    req = types.SimpleNamespace(text="hi", voice="af_sky", speed=1.1, save=False)
    result = KokoroEngine().synthesize(req, {})
    assert result["status"] == "playing"
    assert captured == {"text": "hi", "voice": "af_sky", "speed": 1.1, "save": False}


def test_kokoro_voices_come_from_tts_engine():
    assert KokoroEngine().list_voices() == tts_engine.list_voices_labeled()

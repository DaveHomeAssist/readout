"""Tests for the pluggable engine registry."""
from __future__ import annotations

import types

import tts_engine
from engines import registry
from engines.elevenlabs import ElevenLabsEngine
from engines.kokoro import KokoroEngine
from engines.openai import OpenAIEngine


def test_registry_resolves_known_engines():
    assert isinstance(registry.get("kokoro"), KokoroEngine)
    assert isinstance(registry.get("openai"), OpenAIEngine)
    assert isinstance(registry.get("elevenlabs"), ElevenLabsEngine)
    assert set(registry.names()) == {"kokoro", "openai", "elevenlabs"}


def test_registry_unknown_falls_back_to_default():
    assert registry.get("nonsense").name == "kokoro"
    assert registry.get(None).name == "kokoro"


def test_catalogue_shape_and_capabilities():
    catalogue = {engine["name"]: engine for engine in registry.catalogue()}
    assert set(catalogue) == {"kokoro", "openai", "elevenlabs"}
    for entry in catalogue.values():
        assert {
            "name",
            "label",
            "is_local",
            "requires_key",
            "supports_blend",
            "voices",
        } <= entry.keys()
        assert isinstance(entry["voices"], list) and entry["voices"]
        assert {"id", "label"} <= entry["voices"][0].keys()

    assert catalogue["kokoro"]["is_local"] is True
    assert catalogue["kokoro"]["requires_key"] is None
    assert catalogue["kokoro"]["supports_blend"] is True
    assert catalogue["openai"]["is_local"] is False
    assert catalogue["openai"]["requires_key"] == "openai_api_key"
    assert catalogue["elevenlabs"]["is_local"] is False
    assert catalogue["elevenlabs"]["requires_key"] == "elevenlabs_api_key"


def test_kokoro_engine_delegates_to_tts_engine(monkeypatch):
    captured = {}

    def fake_speak(**kwargs):
        captured.update(kwargs)
        return {"status": "playing", "voice": kwargs["voice"]}

    monkeypatch.setattr(tts_engine, "speak", fake_speak)
    req = types.SimpleNamespace(
        text="hi",
        voice="af_sky",
        speed=1.1,
        save=False,
        allow_always_save=False,
    )
    result = KokoroEngine().synthesize(req, {})

    assert result["status"] == "playing"
    assert captured == {
        "text": "hi",
        "voice": "af_sky",
        "speed": 1.1,
        "save": False,
        "allow_always_save": False,
    }


def test_kokoro_voices_come_from_tts_engine():
    assert KokoroEngine().list_voices() == tts_engine.list_voices_labeled()

"""Tests for the OpenAI / ElevenLabs fallbacks in server.py.

The third-party SDKs (openai, requests) are injected as fakes via sys.modules,
and the shared tts_engine audio helpers are stubbed, so no network or audio
hardware is touched.
"""
from __future__ import annotations

import sys
import types

import pytest

import server
import tts_engine


@pytest.fixture
def stub_audio(monkeypatch):
    """Stub the shared playback/save helpers and record their calls."""
    rec = types.SimpleNamespace(played=[], saved=[], decoded=(["pcm"], 24000))
    monkeypatch.setattr(tts_engine, "read_audio", lambda raw: rec.decoded)
    monkeypatch.setattr(tts_engine, "play_audio", lambda data, sr: rec.played.append((data, sr)))
    monkeypatch.setattr(tts_engine, "save_wav", lambda data, sr: rec.saved.append((data, sr)) or "/tmp/out.wav")
    return rec


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _install_fake_openai(monkeypatch):
    calls = {}

    class FakeSpeech:
        def create(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(content=b"WAVDATA")

    class FakeClient:
        def __init__(self, api_key=None):
            calls["api_key"] = api_key
            self.audio = types.SimpleNamespace(speech=FakeSpeech())

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = FakeClient
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    return calls


def test_openai_plays_and_requests_wav(monkeypatch, stub_audio):
    calls = _install_fake_openai(monkeypatch)
    req = server.SpeakRequest(text="hello", voice="nova", speed=1.2)
    result = server._speak_openai(req, {"openai_api_key": "sk-x"})

    assert result == {"status": "playing", "engine": "openai"}
    assert calls["response_format"] == "wav"   # reliable soundfile decode
    assert calls["voice"] == "nova"
    assert calls["speed"] == 1.2
    assert calls["api_key"] == "sk-x"
    assert stub_audio.played == [(["pcm"], 24000)]


def test_openai_saves_when_requested(monkeypatch, stub_audio):
    _install_fake_openai(monkeypatch)
    req = server.SpeakRequest(text="hi", save=True)
    result = server._speak_openai(req, {"openai_api_key": "sk-x"})
    assert result["saved_to"] == "/tmp/out.wav"
    assert stub_audio.saved


def test_openai_errors_are_caught(monkeypatch, stub_audio):
    fake_openai = types.ModuleType("openai")

    class Boom:
        def __init__(self, api_key=None):
            raise RuntimeError("bad key")

    fake_openai.OpenAI = Boom
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    result = server._speak_openai(server.SpeakRequest(text="hi"), {"openai_api_key": ""})
    assert result["status"] == "error"
    assert "bad key" in result["message"]


# ── ElevenLabs ────────────────────────────────────────────────────────────────

def _install_fake_requests(monkeypatch, *, ok=True, status_code=200, text="", content=b"AUDIO"):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return types.SimpleNamespace(ok=ok, status_code=status_code, text=text, content=content)

    fake_requests = types.ModuleType("requests")
    fake_requests.post = fake_post
    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    return captured


def test_elevenlabs_plays_on_success(monkeypatch, stub_audio):
    captured = _install_fake_requests(monkeypatch)
    req = server.SpeakRequest(text="hello", voice="Rachel")
    result = server._speak_elevenlabs(req, {"elevenlabs_api_key": "el-key"})

    assert result == {"status": "playing", "engine": "elevenlabs"}
    assert captured["headers"]["xi-api-key"] == "el-key"
    assert captured["json"]["text"] == "hello"
    assert "Rachel" in captured["url"]
    assert stub_audio.played == [(["pcm"], 24000)]


def test_elevenlabs_surfaces_http_error(monkeypatch, stub_audio):
    _install_fake_requests(monkeypatch, ok=False, status_code=401, text='{"detail":"unauthorized"}')
    result = server._speak_elevenlabs(server.SpeakRequest(text="hi"), {"elevenlabs_api_key": "bad"})
    assert result["status"] == "error"
    assert "401" in result["message"]
    assert "unauthorized" in result["message"]
    # On error we must not attempt playback.
    assert stub_audio.played == []


def test_elevenlabs_saves_when_requested(monkeypatch, stub_audio):
    _install_fake_requests(monkeypatch)
    req = server.SpeakRequest(text="hi", save=True)
    result = server._speak_elevenlabs(req, {"elevenlabs_api_key": "el-key"})
    assert result["saved_to"] == "/tmp/out.wav"
    assert stub_audio.saved


def test_elevenlabs_uses_default_voice_when_unset(monkeypatch, stub_audio):
    captured = _install_fake_requests(monkeypatch)
    server._speak_elevenlabs(server.SpeakRequest(text="hi"), {"elevenlabs_api_key": "el-key"})
    assert "21m00Tcm4TlvDq8ikWAM" in captured["url"]  # Rachel default

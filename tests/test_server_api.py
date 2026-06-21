"""Endpoint tests for server.py via FastAPI TestClient.

Engine work is monkeypatched so no audio/model code runs.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server
import tts_engine


@pytest.fixture
def client(isolated_config):
    return TestClient(server.app)


# ── Routing / static ──────────────────────────────────────────────────────────

def test_root_redirects_to_control(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/control"


def test_control_panel_serves_html(client):
    r = client.get("/control")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "ReadOut Control Panel" in r.text


# ── /status ───────────────────────────────────────────────────────────────────

def test_status_ready(client, monkeypatch):
    monkeypatch.setattr(tts_engine, "is_loading", lambda: False)
    monkeypatch.setattr(tts_engine, "is_first_run", lambda: False)
    monkeypatch.setattr(tts_engine, "get_load_error", lambda: None)
    data = client.get("/status").json()
    assert data["status"] == "ready"
    assert data["model_ready"] is True
    assert data["engine"] == "kokoro"
    assert data["version"] == "1.0.0"


def test_status_loading(client, monkeypatch):
    monkeypatch.setattr(tts_engine, "is_loading", lambda: True)
    monkeypatch.setattr(tts_engine, "is_first_run", lambda: True)
    monkeypatch.setattr(tts_engine, "get_load_error", lambda: None)
    data = client.get("/status").json()
    assert data["status"] == "loading"
    assert data["model_ready"] is False


# ── /voices ───────────────────────────────────────────────────────────────────

def test_voices_returns_catalogue(client):
    data = client.get("/voices").json()
    assert isinstance(data["voices"], list)
    assert {"id", "label"} <= data["voices"][0].keys()


# ── /speak routing ────────────────────────────────────────────────────────────

def test_speak_defaults_to_kokoro(client, monkeypatch):
    captured = {}

    def fake_speak(text, voice, speed, save):
        captured.update(text=text, voice=voice, speed=speed, save=save)
        return {"status": "playing", "voice": voice}

    monkeypatch.setattr(tts_engine, "speak", fake_speak)
    r = client.post("/speak", json={"text": "hi", "voice": "af_sky", "speed": 1.1})
    assert r.status_code == 200
    assert r.json()["status"] == "playing"
    assert captured == {"text": "hi", "voice": "af_sky", "speed": 1.1, "save": False}


def test_speak_routes_to_openai_when_configured(client, monkeypatch):
    import config
    config.set_config({"engine": "openai"})
    monkeypatch.setattr(server, "_speak_openai", lambda req, cfg: {"status": "playing", "engine": "openai"})
    r = client.post("/speak", json={"text": "hi"})
    assert r.json() == {"status": "playing", "engine": "openai"}


def test_speak_routes_to_elevenlabs_when_configured(client, monkeypatch):
    import config
    config.set_config({"engine": "elevenlabs"})
    monkeypatch.setattr(server, "_speak_elevenlabs", lambda req, cfg: {"status": "playing", "engine": "elevenlabs"})
    r = client.post("/speak", json={"text": "hi"})
    assert r.json() == {"status": "playing", "engine": "elevenlabs"}


def test_speak_requires_text_field(client):
    r = client.post("/speak", json={"voice": "af_heart"})
    assert r.status_code == 422  # pydantic validation: text is required


# ── /stop ─────────────────────────────────────────────────────────────────────

def test_stop_calls_engine(client, monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(tts_engine, "stop_audio", lambda: calls.__setitem__("n", calls["n"] + 1))
    r = client.post("/stop")
    assert r.json() == {"status": "stopped"}
    assert calls["n"] == 1


# ── PATCH /config (the security-critical one) ─────────────────────────────────

def test_patch_config_redacts_api_keys(client):
    r = client.patch("/config", json={"openai_api_key": "sk-live-secret", "voice": "am_adam"})
    body = r.json()
    assert body["status"] == "updated"
    assert body["config"]["openai_api_key"] == "***"
    assert body["config"]["voice"] == "am_adam"
    # Plaintext secret must never appear anywhere in the response body.
    assert "sk-live-secret" not in r.text


def test_patch_config_redacts_elevenlabs_key(client):
    r = client.patch("/config", json={"elevenlabs_api_key": "el-secret-xyz"})
    assert r.json()["config"]["elevenlabs_api_key"] == "***"
    assert "el-secret-xyz" not in r.text


def test_patch_config_persists_secret_even_though_redacted(client, isolated_config):
    import json
    client.patch("/config", json={"openai_api_key": "sk-persist"})
    on_disk = json.loads(isolated_config.read_text(encoding="utf-8"))
    # Redaction is response-only; the daemon still needs the real key.
    assert on_disk["openai_api_key"] == "sk-persist"


def test_patch_config_ignores_unset_fields(client):
    import config
    config.set_config({"voice": "bf_emma"})
    client.patch("/config", json={"speed": 1.5})  # voice not included
    assert config.get_config()["voice"] == "bf_emma"
    assert config.get_config()["speed"] == 1.5


def test_empty_key_is_not_redacted_to_stars(client):
    # An empty/unset key should stay empty, not render as "***".
    r = client.patch("/config", json={"voice": "af_heart"})
    assert r.json()["config"]["openai_api_key"] == ""

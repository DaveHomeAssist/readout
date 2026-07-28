"""End-to-end API tests against a live uvicorn server (real sockets).

Mirrors the in-process endpoint suite but proves the contract holds through a
real HTTP stack: routing, redirects, JSON (de)serialisation, validation, and —
uniquely — that PATCH /config round-trips secrets to an actual file on disk
while redacting them in the response body.
"""
from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.e2e


# ── Routing / static ──────────────────────────────────────────────────────────

def test_root_redirects_to_control(live_server):
    r = live_server.get("/")
    assert r.status in (302, 307)
    assert r.headers["location"] == "/control"


def test_control_panel_serves_html(live_server):
    r = live_server.get("/control")
    assert r.status == 200
    assert "text/html" in r.headers["content-type"]
    assert "ReadOut Control Panel" in r.body


# ── /status, /voices ──────────────────────────────────────────────────────────

def test_status_reports_version_and_engine(live_server):
    data = live_server.get("/status").json()
    assert data["version"] == "1.0.0"
    assert data["engine"] == "kokoro"
    assert data["status"] in ("ready", "loading")
    assert data["model_ready"] is False  # temp HOME has no .model_ready flag


def test_voices_returns_catalogue(live_server):
    data = live_server.get("/voices").json()
    assert isinstance(data["voices"], list) and data["voices"]
    assert {"id", "label"} <= data["voices"][0].keys()


# ── /speak dispatch (Kokoro path stubbed in the fixture) ──────────────────────

def test_speak_dispatches_to_engine(live_server):
    r = live_server.post("/speak", json_body={"text": "hello", "voice": "af_sky", "speed": 1.1})
    body = r.json()
    assert r.status == 200
    assert body["status"] == "playing"
    assert body["voice"] == "af_sky"
    assert body["speed"] == 1.1


def test_speak_requires_text(live_server):
    r = live_server.post("/speak", json_body={"voice": "af_heart"})
    assert r.status == 422  # pydantic: text is required


def test_stop_returns_stopped(live_server):
    r = live_server.post("/stop")
    assert r.json() == {"status": "stopped"}


# ── PATCH /config: redaction over the wire + real file round-trip ─────────────

def test_patch_config_redacts_in_response_but_persists_to_disk(live_server):
    r = live_server.patch("/config", json_body={"openai_api_key": "sk-live-e2e", "voice": "am_adam"})
    body = r.json()
    assert body["status"] == "updated"
    assert body["config"]["openai_api_key"] == "***"
    assert body["config"]["voice"] == "am_adam"
    assert "sk-live-e2e" not in r.body  # plaintext never crosses the wire

    # The daemon still needs the real key, so it must reach the config file.
    on_disk = json.loads(open(live_server.config_path, encoding="utf-8").read())
    assert on_disk["openai_api_key"] == "sk-live-e2e"


def test_patch_config_unset_secret_is_empty_not_stars(live_server):
    r = live_server.patch("/config", json_body={"voice": "af_heart"})
    assert r.json()["config"]["elevenlabs_api_key"] == ""

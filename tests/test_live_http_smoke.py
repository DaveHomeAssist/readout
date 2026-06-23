"""Live loopback HTTP smoke tests for the source server.

These tests start uvicorn in-process on a temporary loopback port. They cover
real HTTP middleware behavior without launching a separate Python process.
"""
from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

import config
from dependency_check import DependencyIssue
import server
import tts_engine

uvicorn = pytest.importorskip("uvicorn")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"server did not bind to port {port}")


@pytest.fixture
def live_server(isolated_config, monkeypatch):
    monkeypatch.setattr(tts_engine, "is_loading", lambda: False)
    monkeypatch.setattr(tts_engine, "is_first_run", lambda: False)
    monkeypatch.setattr(tts_engine, "get_load_error", lambda: None)
    monkeypatch.setattr(server, "check_dependencies", lambda: [])
    monkeypatch.setattr(tts_engine, "speak", lambda **_kwargs: {"status": "playing"})
    monkeypatch.setattr(tts_engine, "stop_audio", lambda: None)

    port = _free_port()
    config.set_config({"port": port})
    uvicorn_config = uvicorn.Config(
        server.app,
        host="127.0.0.1",
        port=port,
        log_level="critical",
        loop="asyncio",
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()
    _wait_for_port(port)

    yield f"http://127.0.0.1:{port}"

    uvicorn_server.should_exit = True
    thread.join(timeout=5)


def _build_request(base_url: str, path: str, *, method: str = "GET", body: dict | None = None, origin: str | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if origin:
        headers["Origin"] = origin
    return urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )


def _request_json(base_url: str, path: str, *, method: str = "GET", body: dict | None = None, origin: str | None = None):
    request = _build_request(base_url, path, method=method, body=body, origin=origin)
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, response.headers, json.loads(response.read().decode("utf-8"))


def _request_error(base_url: str, path: str, *, method: str = "GET", body: dict | None = None, origin: str | None = None):
    request = _build_request(base_url, path, method=method, body=body, origin=origin)
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(request, timeout=5)
    return exc_info.value


def test_live_source_server_smoke_checks_core_non_audio_endpoints(live_server):
    status_code, _headers, status = _request_json(live_server, "/status")
    assert status_code == 200
    assert status["status"] == "ready"
    assert status["dependency_issues"] == []

    status_code, _headers, voices = _request_json(live_server, "/voices")
    assert status_code == 200
    assert {"voices", "engines"} <= voices.keys()
    assert [engine["name"] for engine in voices["engines"]] == ["kokoro", "openai", "elevenlabs"]

    status_code, _headers, history = _request_json(live_server, "/history")
    assert status_code == 200
    assert history == {"enabled": False, "history": []}

    with urllib.request.urlopen(f"{live_server}/control", timeout=5) as response:
        html = response.read().decode("utf-8")
    assert response.status == 200
    assert "ReadOut Control Panel" in html
    assert "/preview" in html


def test_live_source_server_rejects_disallowed_origin_before_side_effects(live_server, monkeypatch):
    calls = {"speak": 0}
    monkeypatch.setattr(
        tts_engine,
        "speak",
        lambda **_kwargs: calls.__setitem__("speak", calls["speak"] + 1) or {"status": "playing"},
    )

    error = _request_error(
        live_server,
        "/speak",
        method="POST",
        body={"text": "blocked"},
        origin="https://evil.com",
    )

    assert error.code == 403
    assert "access-control-allow-origin" not in error.headers
    assert calls == {"speak": 0}


def test_live_source_server_cors_origin_matrix(live_server):
    configured_extension = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"
    config.set_config({"allowed_origins": [configured_extension]})

    for origin in [
        "http://localhost",
        "http://127.0.0.1:7778",
        configured_extension,
    ]:
        status_code, headers, _status = _request_json(live_server, "/status", origin=origin)
        assert status_code == 200
        assert headers["access-control-allow-origin"] == origin

    for origin in [
        "https://evil.com",
        "http://localhost.evil.com",
        "chrome-extension://zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
        "null",
    ]:
        error = _request_error(live_server, "/status", origin=origin)
        assert error.code == 403
        assert "access-control-allow-origin" not in error.headers


def test_live_source_server_redacts_config_keys_and_persists_history_controls(live_server):
    _status_code, _headers, body = _request_json(
        live_server,
        "/config",
        method="PATCH",
        body={
            "openai_api_key": "sk-live-secret",
            "elevenlabs_api_key": "el-live-secret",
            "history_enabled": True,
            "history_limit": 500,
        },
    )

    assert body["config"]["openai_api_key"] == "***"
    assert body["config"]["elevenlabs_api_key"] == "***"
    assert "sk-live-secret" not in json.dumps(body)
    assert body["config"]["history_enabled"] is True
    assert body["config"]["history_limit"] == 100

    _status_code, _headers, history = _request_json(live_server, "/history")
    assert history == {"enabled": True, "history": []}


def test_live_source_server_preview_is_request_local_and_does_not_save(live_server, monkeypatch):
    captured = {}

    def fake_speak(**kwargs):
        captured.update(kwargs)
        return {"status": "playing"}

    monkeypatch.setattr(tts_engine, "speak", fake_speak)
    config.set_config({"always_save": True, "voice": "bf_emma", "history_enabled": True})

    _status_code, _headers, body = _request_json(
        live_server,
        "/preview",
        method="POST",
        body={"voice": "af_sky", "speed": 1.2},
    )

    assert body == {"status": "playing", "preview": True}
    assert captured == {
        "text": server.PREVIEW_TEXT,
        "voice": "af_sky",
        "speed": 1.2,
        "save": False,
        "allow_always_save": False,
    }
    assert config.get_config()["voice"] == "bf_emma"
    assert "saved_to" not in body

    _status_code, _headers, history = _request_json(live_server, "/history")
    assert history == {"enabled": True, "history": []}


def test_live_source_server_reports_dependency_issue_shape(live_server, monkeypatch):
    monkeypatch.setattr(
        server,
        "check_dependencies",
        lambda: [
            DependencyIssue(
                id="espeak-ng",
                severity="error",
                message="The espeak-ng executable was not found on PATH.",
                fix="Install espeak-ng.",
            )
        ],
    )

    _status_code, _headers, status = _request_json(live_server, "/status")

    assert status["dependency_issues"] == [
        {
            "id": "espeak-ng",
            "severity": "error",
            "message": "The espeak-ng executable was not found on PATH.",
            "fix": "Install espeak-ng.",
        }
    ]

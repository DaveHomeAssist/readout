"""CORS / Origin policy tests — the regression that prompted this work.

A wildcard policy let any visited website drive the local 127.0.0.1:7778
daemon. These tests pin the contract: trusted browser origins are explicit,
and disallowed origins are rejected before endpoint side effects can run.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import config
import server
import tts_engine


ALLOWED = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:7778",
]

CONFIGURED_EXTENSION = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"

DISALLOWED = [
    "https://evil.com",
    "http://evil.com",
    "http://localhost.evil.com",   # suffix attack on the localhost prefix
    "https://localhost",           # https is not a configured dev origin
    "chrome-extension://zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
    "null",
]


@pytest.fixture
def client(isolated_config):
    return TestClient(server.app)


def test_policy_is_not_wildcard(client):
    # The whole point: the allowed-origin echo must never be "*".
    r = client.get("/status", headers={"Origin": "https://evil.com"})
    assert r.headers.get("access-control-allow-origin") != "*"


@pytest.mark.parametrize("path", ["/docs", "/openapi.json", "/redoc"])
def test_interactive_api_docs_are_disabled(client, path):
    r = client.get(path)
    assert r.status_code == 404


def test_non_loopback_host_is_rejected(client):
    r = client.get("/status", headers={"Host": "evil.com"})
    assert r.status_code == 400


@pytest.mark.parametrize("origin", ALLOWED)
def test_allowed_origins_get_cors_header(client, origin):
    r = client.get("/status", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin


@pytest.mark.parametrize("origin", DISALLOWED)
def test_disallowed_origins_get_no_cors_header(client, origin):
    r = client.get("/status", headers={"Origin": origin})
    assert r.status_code == 403
    assert "access-control-allow-origin" not in r.headers


def test_configured_extension_origin_gets_cors_header(client):
    config.set_config({"allowed_origins": [CONFIGURED_EXTENSION]})
    r = client.get("/status", headers={"Origin": CONFIGURED_EXTENSION})
    assert r.headers.get("access-control-allow-origin") == CONFIGURED_EXTENSION


def test_extension_origin_can_be_allowed_by_env(client, monkeypatch):
    monkeypatch.setenv(server._ALLOWED_ORIGINS_ENV, CONFIGURED_EXTENSION)
    r = client.get("/status", headers={"Origin": CONFIGURED_EXTENSION})
    assert r.headers.get("access-control-allow-origin") == CONFIGURED_EXTENSION


def test_wildcard_origin_config_is_ignored(client):
    config.set_config({"allowed_origins": ["*"]})
    r = client.get("/status", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403
    assert "access-control-allow-origin" not in r.headers


def test_preflight_allows_patch_from_configured_extension(client):
    config.set_config({"allowed_origins": [CONFIGURED_EXTENSION]})
    r = client.options(
        "/config",
        headers={
            "Origin": CONFIGURED_EXTENSION,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 204
    assert r.headers.get("access-control-allow-origin") == CONFIGURED_EXTENSION
    assert "PATCH" in r.headers.get("access-control-allow-methods", "")


def test_preflight_blocked_for_disallowed_origin(client):
    r = client.options(
        "/config",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "PATCH",
        },
    )
    assert r.status_code == 403
    assert "access-control-allow-origin" not in r.headers


def test_preflight_blocks_disallowed_header(client):
    r = client.options(
        "/config",
        headers={
            "Origin": "http://localhost:7778",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "x-api-key",
        },
    )
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_preflight_allows_delete_history_from_local_origin(client):
    r = client.options(
        "/history",
        headers={
            "Origin": "http://localhost:7778",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert r.status_code == 204
    assert r.headers.get("access-control-allow-origin") == "http://localhost:7778"
    assert "DELETE" in r.headers.get("access-control-allow-methods", "")


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/status", None),
        ("GET", "/voices", None),
        ("POST", "/speak", {"text": "should not speak"}),
        ("POST", "/preview", {"voice": "af_heart"}),
        ("POST", "/stop", None),
        ("PATCH", "/config", {"voice": "am_adam"}),
        ("DELETE", "/history", None),
    ],
)
def test_disallowed_origin_rejected_before_endpoint_side_effects(
    client,
    monkeypatch,
    method,
    path,
    json_body,
):
    calls = {"speak": 0, "stop": 0}

    def fake_speak(**_kwargs):
        calls["speak"] += 1
        return {"status": "playing"}

    monkeypatch.setattr(tts_engine, "speak", fake_speak)
    monkeypatch.setattr(tts_engine, "stop_audio", lambda: calls.__setitem__("stop", calls["stop"] + 1))

    r = client.request(
        method,
        path,
        headers={"Origin": "https://evil.com"},
        json=json_body,
    )

    assert r.status_code == 403
    assert "access-control-allow-origin" not in r.headers
    assert calls == {"speak": 0, "stop": 0}
    assert config.get_config()["voice"] == "af_heart"

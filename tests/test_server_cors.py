"""CORS policy tests — the regression that prompted this work.

A wildcard policy let any visited website drive the local 127.0.0.1:7778
daemon. These tests pin the contract: only the Chrome extension and local
dev origins are allowed.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server

client = TestClient(server.app)

ALLOWED = [
    "chrome-extension://abcdefghijklmnopabcdefghijklmnop",
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:7778",
]

DISALLOWED = [
    "https://evil.com",
    "http://evil.com",
    "http://localhost.evil.com",   # suffix attack on the localhost prefix
    "https://localhost",           # https is not a configured dev origin
    "null",
]


def test_policy_is_not_wildcard():
    # The whole point: the allowed-origin echo must never be "*".
    r = client.get("/status", headers={"Origin": "https://evil.com"})
    assert r.headers.get("access-control-allow-origin") != "*"


@pytest.mark.parametrize("origin", ALLOWED)
def test_allowed_origins_get_cors_header(origin):
    r = client.get("/status", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin


@pytest.mark.parametrize("origin", DISALLOWED)
def test_disallowed_origins_get_no_cors_header(origin):
    r = client.get("/status", headers={"Origin": origin})
    assert "access-control-allow-origin" not in r.headers


def test_preflight_allows_patch_from_extension():
    r = client.options(
        "/config",
        headers={
            "Origin": "chrome-extension://abcdefghijklmnopabcdefghijklmnop",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code in (200, 204)
    assert "PATCH" in r.headers.get("access-control-allow-methods", "")


def test_preflight_blocked_for_disallowed_origin():
    r = client.options(
        "/config",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "PATCH",
        },
    )
    assert "access-control-allow-origin" not in r.headers

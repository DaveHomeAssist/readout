"""End-to-end CORS tests against a live uvicorn server.

The in-process CORS suite (tests/test_server_cors.py) already pins the policy
via TestClient. This re-checks the *same* contract over a real socket, so a
divergence between Starlette's test transport and the deployed uvicorn stack
(middleware ordering, preflight short-circuit) can't hide the regression that
issue 002 was about.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e

EXT_ORIGIN = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"

ALLOWED = [EXT_ORIGIN, "http://localhost", "http://localhost:5173", "http://127.0.0.1:7778"]
DISALLOWED = [
    "https://evil.com",
    "http://evil.com",
    "http://localhost.evil.com",  # suffix attack on the localhost prefix
    "https://localhost",          # https is not a configured dev origin
    "null",
]


def test_policy_is_never_wildcard(live_server):
    r = live_server.get("/status", headers={"Origin": "https://evil.com"})
    assert r.headers.get("access-control-allow-origin") != "*"


@pytest.mark.parametrize("origin", ALLOWED)
def test_allowed_origin_is_echoed(live_server, origin):
    r = live_server.get("/status", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin


@pytest.mark.parametrize("origin", DISALLOWED)
def test_disallowed_origin_gets_no_cors_header(live_server, origin):
    r = live_server.get("/status", headers={"Origin": origin})
    assert "access-control-allow-origin" not in r.headers


def test_preflight_allows_patch_from_extension(live_server):
    r = live_server.options(
        "/config",
        headers={
            "Origin": EXT_ORIGIN,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status in (200, 204)
    assert "PATCH" in r.headers.get("access-control-allow-methods", "")
    assert r.headers.get("access-control-allow-origin") == EXT_ORIGIN


def test_preflight_blocked_for_disallowed_origin(live_server):
    r = live_server.options(
        "/config",
        headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "PATCH"},
    )
    assert "access-control-allow-origin" not in r.headers

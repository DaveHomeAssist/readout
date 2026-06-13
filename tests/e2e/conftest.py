"""End-to-end harness fixtures — boot the real server over a real socket.

The in-process unit suite (tests/test_server_*.py) exercises `server.app` via
Starlette's TestClient, which never opens a socket and never runs uvicorn's
lifespan. This layer fills that gap: it launches the actual ASGI app under
uvicorn in a background thread on an ephemeral port and drives it with a plain
stdlib HTTP client. That validates the parts only a live process can prove —
the server binds and serves, CORS middleware behaves identically over the wire,
config round-trips to a real file, and `GET /` really redirects.

Heavy leaf calls (the Kokoro `speak()` / audio playback) are stubbed so the
harness needs neither torch/kokoro nor audio hardware and runs in CI.
"""
from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

# The e2e layer needs the real server, so skip cleanly if it isn't installed
# (e.g. a minimal `pip install pytest` unit-only environment).
pytest.importorskip("uvicorn")

pytestmark = pytest.mark.e2e


def _free_port() -> int:
    """Grab an OS-assigned free TCP port on the loopback interface."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Disable auto-following so tests can assert on 3xx responses directly."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Resp:
    """Lightweight response wrapper. `headers` keys are lower-cased."""

    def __init__(self, status: int, headers: dict, body: str):
        self.status = status
        self.headers = headers
        self.body = body

    def json(self):
        return json.loads(self.body)


class Client:
    """Minimal real-socket HTTP client (stdlib only — no httpx/requests)."""

    def __init__(self, base: str, config_path: str | None = None):
        self.base = base
        self.config_path = config_path
        self._opener = urllib.request.build_opener(_NoRedirect)

    def request(self, method, path, json_body=None, headers=None) -> Resp:
        data = None
        h = dict(headers or {})
        if json_body is not None:
            data = json.dumps(json_body).encode()
            h.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        try:
            r = self._opener.open(req, timeout=10)
            status, raw_headers, body = r.status, r.getheaders(), r.read().decode()
        except urllib.error.HTTPError as e:
            # 4xx/5xx still carry headers we want to inspect (CORS preflight 400).
            status, raw_headers, body = e.code, list(e.headers.items()), e.read().decode()
        return Resp(status, {k.lower(): v for k, v in raw_headers}, body)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def options(self, path, **kw):
        return self.request("OPTIONS", path, **kw)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Run `server.app` under uvicorn in a thread; yield a Client for it.

    Module-scoped: one real server per e2e test module (its own port + temp
    ~/.readout). Config/model paths and the heavy speak()/stop helpers are
    patched before the server serves a single request.
    """
    import uvicorn

    import config
    import tts_engine
    import server

    cfg_dir = tmp_path_factory.mktemp("readout_home") / ".readout"
    cfg_path = cfg_dir / "config.json"

    mp = pytest.MonkeyPatch()
    mp.setattr(config, "CONFIG_DIR", str(cfg_dir))
    mp.setattr(config, "CONFIG_PATH", str(cfg_path))
    mp.setattr(tts_engine, "MODEL_READY_FLAG", str(cfg_dir / ".model_ready"))
    # Stub the heavy Kokoro path + stop so /speak and /stop work without torch,
    # the 300 MB model download, or audio hardware. Echo inputs back so the
    # dispatch wiring (server → tts_engine) stays observable end to end.
    mp.setattr(
        tts_engine,
        "speak",
        lambda text, voice=None, speed=None, save=False: {
            "status": "playing",
            "engine": "kokoro",
            "voice": voice or "af_heart",
            "speed": speed or 1.0,
            "save": save,
        },
    )
    mp.setattr(tts_engine, "stop_audio", lambda: None)

    port = _free_port()
    uconf = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(uconf)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    client = Client(base, config_path=str(cfg_path))

    # Wait for the socket to start serving (uvicorn boot is ~0.2-0.5s).
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if client.get("/status").status == 200:
                break
        except urllib.error.URLError:
            time.sleep(0.1)
    else:
        srv.should_exit = True
        thread.join(timeout=5)
        mp.undo()
        raise RuntimeError(f"live server never became ready on {base}")

    try:
        yield client
    finally:
        srv.should_exit = True
        thread.join(timeout=5)
        mp.undo()

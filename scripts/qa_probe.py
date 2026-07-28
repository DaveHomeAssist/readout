#!/usr/bin/env python3
"""qa_probe.py — manual QA driver for a RUNNING ReadOut daemon.

Unlike the pytest suites (which stub audio/model), this talks to the real
daemon you started with `python main.py`, so `speak` plays real audio through
the real engine. Use it to sanity-check a dev build or a packaged .app, and to
verify the CORS lockdown from the command line.

Stdlib only — no install needed. Run `python main.py` first, then:

    python scripts/qa_probe.py status
    python scripts/qa_probe.py voices
    python scripts/qa_probe.py speak "Hello from ReadOut" --voice af_sky --speed 1.1
    python scripts/qa_probe.py stop
    python scripts/qa_probe.py config --engine openai --openai-key sk-...
    python scripts/qa_probe.py cors --origin https://evil.com   # expect: BLOCKED

Add --url http://127.0.0.1:7778 to target a non-default host/port.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:7778"


def _call(url, path, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if data:
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url + path, data=data, headers=h, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status, {k.lower(): v for k, v in r.getheaders()}, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read().decode()
    except urllib.error.URLError as e:
        print(f"ERROR: cannot reach {url} — is the daemon running? ({e.reason})", file=sys.stderr)
        raise SystemExit(2)


def _show(status, body):
    print(f"HTTP {status}")
    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body[:500])


def cmd_status(a):
    _show(*_call(a.url, "/status")[::2])


def cmd_voices(a):
    _show(*_call(a.url, "/voices")[::2])


def cmd_speak(a):
    body = {"text": a.text, "save": a.save}
    if a.voice:
        body["voice"] = a.voice
    if a.speed:
        body["speed"] = a.speed
    _show(*_call(a.url, "/speak", "POST", body)[::2])


def cmd_stop(a):
    _show(*_call(a.url, "/stop", "POST")[::2])


def cmd_config(a):
    body = {}
    if a.engine:
        body["engine"] = a.engine
    if a.voice:
        body["voice"] = a.voice
    if a.openai_key is not None:
        body["openai_api_key"] = a.openai_key
    if a.elevenlabs_key is not None:
        body["elevenlabs_api_key"] = a.elevenlabs_key
    if not body:
        print("Nothing to update. Pass --engine/--voice/--openai-key/--elevenlabs-key.")
        return
    status, _, resp = _call(a.url, "/config", "PATCH", body)
    _show(status, resp)
    # Defensive check: the response must never echo a plaintext key.
    for secret in (a.openai_key, a.elevenlabs_key):
        if secret and secret in resp:
            print("\n*** WARNING: a plaintext API key appeared in the response! ***")


def cmd_cors(a):
    """Send an Origin header and report whether CORS would allow it."""
    status, headers, _ = _call(a.url, "/status", headers={"Origin": a.origin})
    acao = headers.get("access-control-allow-origin")
    if acao == a.origin:
        print(f"ALLOWED  — server echoed access-control-allow-origin: {acao}")
    elif acao == "*":
        print("WILDCARD — server returned '*' (this is the issue-002 regression!)")
        raise SystemExit(1)
    else:
        print(f"BLOCKED  — no matching access-control-allow-origin for {a.origin!r}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=DEFAULT_URL, help=f"daemon base URL (default {DEFAULT_URL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("voices").set_defaults(func=cmd_voices)
    sub.add_parser("stop").set_defaults(func=cmd_stop)

    sp = sub.add_parser("speak")
    sp.add_argument("text")
    sp.add_argument("--voice")
    sp.add_argument("--speed", type=float)
    sp.add_argument("--save", action="store_true")
    sp.set_defaults(func=cmd_speak)

    cp = sub.add_parser("config")
    cp.add_argument("--engine", choices=["kokoro", "openai", "elevenlabs"])
    cp.add_argument("--voice")
    cp.add_argument("--openai-key", dest="openai_key")
    cp.add_argument("--elevenlabs-key", dest="elevenlabs_key")
    cp.set_defaults(func=cmd_config)

    cc = sub.add_parser("cors")
    cc.add_argument("--origin", required=True, help="e.g. https://evil.com")
    cc.set_defaults(func=cmd_cors)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

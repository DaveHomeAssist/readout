#!/usr/bin/env bash
# smoke.sh — boot the real ASGI app in a subprocess and probe it over HTTP.
#
# Complements the pytest e2e harness (which runs uvicorn in a thread): this
# proves the app starts as a *separate process* via the same entrypoint used in
# production, with an isolated HOME so it never touches your real ~/.readout.
# Requires the runtime deps (fastapi + uvicorn); does NOT need torch/kokoro
# because /status and /voices don't load the model.
#
# Usage: scripts/smoke.sh [port]   (default 7799)
set -euo pipefail

PORT="${1:-7799}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPHOME="$(mktemp -d)"
export HOME="$TMPHOME"        # isolate ~/.readout for this run

cleanup() {
  [ -n "${SRV_PID:-}" ] && kill "$SRV_PID" 2>/dev/null || true
  rm -rf "$TMPHOME"
}
trap cleanup EXIT

cd "$ROOT"
python -m uvicorn server:app --host 127.0.0.1 --port "$PORT" --log-level warning &
SRV_PID=$!

base="http://127.0.0.1:$PORT"
ready=""
for _ in $(seq 1 50); do
  if curl -sf "$base/status" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.2
done
[ -n "$ready" ] || { echo "FAIL: server did not become ready on $base"; exit 1; }

curl -sf "$base/status" | grep -q '"version"' && echo "OK   /status"
curl -sf "$base/voices" | grep -q '"voices"'  && echo "OK   /voices"

# CORS regression guard: a hostile origin must NOT be echoed back.
acao="$(curl -sf -D - -o /dev/null -H 'Origin: https://evil.com' "$base/status" \
        | tr -d '\r' | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2}')"
if [ "$acao" = "*" ] || [ "$acao" = "https://evil.com" ]; then
  echo "FAIL: hostile origin allowed by CORS (got '$acao')"; exit 1
fi
echo "OK   CORS rejects hostile origin"

echo "SMOKE PASSED"

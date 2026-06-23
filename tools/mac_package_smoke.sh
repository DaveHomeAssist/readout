#!/usr/bin/env bash
# macOS packaged-app smoke test.
# Run after ./build_mac.sh produces dist/ReadOut.app.

set -u

APP_PATH="dist/ReadOut.app"
BASE_URL="http://127.0.0.1:7778"
TIMEOUT_SEC=45
INCLUDE_AUDIO=0
SKIP_CORS=0
FAILED=0
APP_LAUNCHED=0
APP_EXECUTABLE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --app)
      APP_PATH="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_SEC="$2"
      shift 2
      ;;
    --include-audio)
      INCLUDE_AUDIO=1
      shift
      ;;
    --skip-cors)
      SKIP_CORS=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

add_result() {
  local check="$1"
  local result="$2"
  local detail="$3"
  printf '| %s | %s | %s |\n' "$check" "$result" "$detail"
  if [ "$result" = "FAIL" ]; then
    FAILED=1
  fi
}

server_ready() {
  curl -fsS "$BASE_URL/status" >/tmp/readout_status_$$.json 2>/dev/null
}

resolve_app_executable() {
  local app_dir
  local app_name
  app_dir="$(cd "$(dirname "$APP_PATH")" && pwd -P)" || return 1
  app_name="$(basename "$APP_PATH")"
  APP_EXECUTABLE="$app_dir/$app_name/Contents/MacOS/ReadOut"
}

app_pids() {
  if [ -n "$APP_EXECUTABLE" ] && [ -x "$APP_EXECUTABLE" ]; then
    pgrep -f "$APP_EXECUTABLE" 2>/dev/null || true
  else
    pgrep -x "ReadOut" 2>/dev/null || true
  fi
}

wait_for_app_shutdown() {
  local timeout="$1"
  local deadline
  local pids
  deadline=$(( $(date +%s) + timeout ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    pids="$(app_pids)"
    if [ -z "$pids" ] && ! server_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

cleanup() {
  rm -f /tmp/readout_status_$$.json
  if [ "$APP_LAUNCHED" -eq 1 ]; then
    osascript -e 'tell application "ReadOut" to quit' >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "| Check | Result | Detail |"
echo "|---|---|---|"

if [ ! -d "$APP_PATH" ]; then
  add_result "App bundle exists" "FAIL" "$APP_PATH"
  exit 1
fi
add_result "App bundle exists" "PASS" "$APP_PATH"
resolve_app_executable

if server_ready; then
  add_result "Port available" "FAIL" "A server is already responding at $BASE_URL"
  exit 1
fi
add_result "Port available" "PASS" "$BASE_URL"

if open -n "$APP_PATH" >/dev/null 2>&1; then
  APP_LAUNCHED=1
  add_result "Launch packaged app" "PASS" "$APP_PATH"
else
  add_result "Launch packaged app" "FAIL" "$APP_PATH"
  exit 1
fi

deadline=$(( $(date +%s) + TIMEOUT_SEC ))
ready=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if server_ready; then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  add_result "Server ready" "FAIL" "No /status response within ${TIMEOUT_SEC}s"
  exit 1
fi
add_result "Server ready" "PASS" "$BASE_URL/status"

status_json="$(cat /tmp/readout_status_$$.json)"
case "$status_json" in
  *'"status"'*'"engine"'*'"dependency_issues"'*)
    add_result "GET /status shape" "PASS" "required fields present"
    ;;
  *)
    add_result "GET /status shape" "FAIL" "missing required fields"
    ;;
esac

voices_json="$(curl -fsS "$BASE_URL/voices" 2>/dev/null || true)"
case "$voices_json" in
  *'"voices"'*'"id"'*'"label"'*)
    add_result "GET /voices" "PASS" "voice rows present"
    ;;
  *)
    add_result "GET /voices" "FAIL" "missing voices/id/label"
    ;;
esac

history_json="$(curl -fsS "$BASE_URL/history" 2>/dev/null || true)"
case "$history_json" in
  *'"enabled"'*'"history"'*)
    add_result "GET /history" "PASS" "privacy shape present"
    ;;
  *)
    add_result "GET /history" "FAIL" "missing enabled/history"
    ;;
esac

control_html="$(curl -fsS "$BASE_URL/control" 2>/dev/null || true)"
for needle in \
  "primary macOS control surface" \
  "Preview Voice" \
  "Speak + Save WAV" \
  "Remember recent reads on this device" \
  "Clear History"
do
  case "$control_html" in
    *"$needle"*) ;;
    *)
      add_result "GET /control" "FAIL" "missing $needle"
      ;;
  esac
done
if [ "$FAILED" -eq 0 ]; then
  add_result "GET /control" "PASS" "required controls present"
fi

if [ "$INCLUDE_AUDIO" -eq 1 ]; then
  preview_json="$(curl -fsS \
    -H 'Content-Type: application/json' \
    -d '{"voice":"af_heart","speed":1.0}' \
    "$BASE_URL/preview" 2>/dev/null || true)"
  case "$preview_json" in
    *'"preview":true'*)
      add_result "POST /preview" "PASS" "preview=true"
      ;;
    *)
      add_result "POST /preview" "FAIL" "preview did not return preview=true"
      ;;
  esac
fi

if [ "$SKIP_CORS" -eq 0 ]; then
  cors_headers="$(curl -sS -i -H 'Origin: https://evil.com' "$BASE_URL/status" 2>/dev/null || true)"
  case "$cors_headers" in
    *"HTTP/"*" 403 "*)
      if printf '%s' "$cors_headers" | grep -qi '^Access-Control-Allow-Origin:'; then
        add_result "Blocked origin" "FAIL" "403 included Access-Control-Allow-Origin"
      else
        add_result "Blocked origin" "PASS" "403 with no allow-origin header"
      fi
      ;;
    *)
      add_result "Blocked origin" "FAIL" "evil origin was not rejected"
      ;;
  esac
else
  add_result "Blocked origin" "SKIP" "--skip-cors set"
fi

if [ "$APP_LAUNCHED" -eq 1 ]; then
  if osascript -e 'tell application "ReadOut" to quit' >/dev/null 2>&1; then
    if wait_for_app_shutdown 20; then
      add_result "App quits cleanly" "PASS" "no app process or server response after quit"
    else
      remaining_pids="$(app_pids)"
      if [ -z "$remaining_pids" ]; then
        remaining_pids="none"
      fi
      add_result "App quits cleanly" "FAIL" "processes=$remaining_pids; server may still be responding"
    fi
  else
    add_result "App quits cleanly" "FAIL" "osascript quit failed"
  fi
  APP_LAUNCHED=0
fi

exit "$FAILED"

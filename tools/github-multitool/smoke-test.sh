#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

SERVER_LOG="/tmp/github-multitool-server.log"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

json_get_bool() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path = sys.argv[1]
key = sys.argv[2]

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

value = data.get(key)
if value is True:
    print("true")
elif value is False:
    print("false")
else:
    print("")
PY
}

check_endpoint() {
  local label="$1"
  local url="$2"
  local output="$3"

  echo
  echo "== $label =="
  curl -fsS "$url" > "$output"
  cat "$output"
  echo
  echo "[PASS] $label"
}

echo "== GitHub multitool smoke test =="

echo
echo "== Python syntax =="
python3 -m py_compile tools/github-multitool/config_validation.py
python3 -m py_compile tools/github-multitool/github_multitool.py
python3 -m py_compile tools/github-multitool/server.py
echo "[PASS] Python syntax"

echo
echo "== CLI health =="
python3 tools/github-multitool/github_multitool.py health > /tmp/github-multitool-cli-health.json
cat /tmp/github-multitool-cli-health.json
echo
echo "[PASS] CLI health"

echo
echo "== CLI repo status =="
python3 tools/github-multitool/github_multitool.py repo-status > /tmp/github-multitool-cli-repo-status.json
cat /tmp/github-multitool-cli-repo-status.json
echo
echo "[PASS] CLI repo status"

repo_private="$(json_get_bool /tmp/github-multitool-cli-repo-status.json isPrivate)"

echo
echo "== CLI strict-private behavior =="
if [[ "$repo_private" == "false" ]]; then
  if python3 tools/github-multitool/github_multitool.py repo-status --strict-private >/tmp/github-multitool-strict-private.json 2>&1; then
    echo "[FAIL] strict-private unexpectedly passed for public repo"
    cat /tmp/github-multitool-strict-private.json
    exit 1
  fi
  cat /tmp/github-multitool-strict-private.json
  echo
  echo "[PASS] strict-private failed as expected for public repo"
else
  python3 tools/github-multitool/github_multitool.py repo-status --strict-private >/tmp/github-multitool-strict-private.json
  cat /tmp/github-multitool-strict-private.json
  echo
  echo "[PASS] strict-private passed for private repo"
fi

echo
echo "== Server startup =="
python3 tools/github-multitool/server.py > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

sleep 1

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "[FAIL] Server did not start"
  cat "$SERVER_LOG"
  exit 1
fi

echo "[PASS] Server process started"

check_endpoint "Server health" "http://127.0.0.1:8765/health" "/tmp/github-multitool-server-health.json"
check_endpoint "Server repo status" "http://127.0.0.1:8765/repo/status" "/tmp/github-multitool-server-repo-status.json"
check_endpoint "Server PR list" "http://127.0.0.1:8765/prs?limit=5" "/tmp/github-multitool-server-prs.json"
check_endpoint "Server issues list" "http://127.0.0.1:8765/issues?limit=5" "/tmp/github-multitool-server-issues.json"
check_endpoint "Server branches list" "http://127.0.0.1:8765/branches?limit=5" "/tmp/github-multitool-server-branches.json"

echo
echo "== Server strict-private route behavior =="
strict_status="$(
  curl -sS -o /tmp/github-multitool-server-strict-private.json \
    -w "%{http_code}" \
    "http://127.0.0.1:8765/repo/status?strict_private=1"
)"
cat /tmp/github-multitool-server-strict-private.json
echo

if [[ "$repo_private" == "false" ]]; then
  if [[ "$strict_status" != "500" ]]; then
    echo "[FAIL] Expected HTTP 500 for public repo strict_private=1, got $strict_status"
    exit 1
  fi
  echo "[PASS] Server strict-private failed as expected for public repo"
else
  if [[ "$strict_status" != "200" ]]; then
    echo "[FAIL] Expected HTTP 200 for private repo strict_private=1, got $strict_status"
    exit 1
  fi
  echo "[PASS] Server strict-private passed for private repo"
fi

echo
echo "== Server write-method rejection =="
post_status="$(
  curl -sS -o /tmp/github-multitool-post-response.json \
    -w "%{http_code}" \
    -X POST \
    "http://127.0.0.1:8765/prs"
)"
cat /tmp/github-multitool-post-response.json
echo

if [[ "$post_status" != "405" ]]; then
  echo "[FAIL] Expected HTTP 405 for POST rejection, got $post_status"
  exit 1
fi

echo "[PASS] POST rejected"

echo
echo "== Final result =="
echo "[PASS] GitHub multitool smoke test completed successfully."

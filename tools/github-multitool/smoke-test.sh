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

echo "== GitHub multitool smoke test =="

echo
echo "== Python syntax =="
python3 -m py_compile tools/github-multitool/github_multitool.py
python3 -m py_compile tools/github-multitool/server.py
echo "[PASS] Python syntax"

echo
echo "== CLI health =="
python3 tools/github-multitool/github_multitool.py health
echo "[PASS] CLI health"

echo
echo "== Server health =="
python3 tools/github-multitool/server.py > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

sleep 1

curl -fsS http://127.0.0.1:8765/health >/tmp/github-multitool-health.json
cat /tmp/github-multitool-health.json
echo
echo "[PASS] Server health"

echo
echo "== Read-only endpoint check =="
curl -fsS http://127.0.0.1:8765/repo/status >/tmp/github-multitool-repo-status.json
cat /tmp/github-multitool-repo-status.json
echo
echo "[PASS] Repo status endpoint"

echo
echo "== Final result =="
echo "[PASS] GitHub multitool smoke test completed successfully."

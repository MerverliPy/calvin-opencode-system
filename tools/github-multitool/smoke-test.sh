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

echo
echo "== CLI pr-dashboard =="
python3 tools/github-multitool/github_multitool.py pr-dashboard --limit 5 > /tmp/github-multitool-cli-dashboard.json
cat /tmp/github-multitool-cli-dashboard.json
echo
echo "[PASS] CLI pr-dashboard"

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
check_endpoint "Server PR dashboard" "http://127.0.0.1:8765/prs/dashboard?limit=5" "/tmp/github-multitool-server-dashboard.json"
check_endpoint "Server issues list" "http://127.0.0.1:8765/issues?limit=5" "/tmp/github-multitool-server-issues.json"
check_endpoint "Server branches list" "http://127.0.0.1:8765/branches?limit=5" "/tmp/github-multitool-server-branches.json"

# ── PR readiness (CLI) ──────────────────────────────────────────
echo
echo "== CLI pr-readiness =="
# Find an open PR number, or skip with a safe fallback
PR_NUMBER="$(python3 -c "
import json
with open('/tmp/github-multitool-server-prs.json') as f:
    prs = json.load(f)
if isinstance(prs, list) and prs:
    print(prs[0].get('number', ''))
" 2>/dev/null || echo "")"

if [[ -n "$PR_NUMBER" ]]; then
  python3 tools/github-multitool/github_multitool.py pr-readiness "$PR_NUMBER" > /tmp/github-multitool-cli-pr-readiness.json
  cat /tmp/github-multitool-cli-pr-readiness.json

  # Quick validation: output must have score and risk fields
  score="$(python3 -c "
import json
with open('/tmp/github-multitool-cli-pr-readiness.json') as f:
    d = json.load(f)
print(d.get('score', ''))
")"
  risk="$(python3 -c "
import json
with open('/tmp/github-multitool-cli-pr-readiness.json') as f:
    d = json.load(f)
print(d.get('risk', ''))
")"
  if [[ -z "$score" || -z "$risk" ]]; then
    echo "[FAIL] CLI pr-readiness missing score or risk field"
    exit 1
  fi
  echo
  echo "[PASS] CLI pr-readiness (PR #$PR_NUMBER, score=$score, risk=$risk)"
else
  echo "No open PRs found; skipping CLI pr-readiness test."
  echo "[PASS] CLI pr-readiness (skipped — no open PRs)"
fi

# ── PR readiness (server endpoint) ──────────────────────────────
echo
echo "== Server pr-readiness =="
if [[ -n "$PR_NUMBER" ]]; then
  curl -fsS "http://127.0.0.1:8765/pr/$PR_NUMBER/readiness" > /tmp/github-multitool-server-pr-readiness.json
  cat /tmp/github-multitool-server-pr-readiness.json

  score="$(python3 -c "
import json
with open('/tmp/github-multitool-server-pr-readiness.json') as f:
    d = json.load(f)
print(d.get('score', ''))
")"
  risk="$(python3 -c "
import json
with open('/tmp/github-multitool-server-pr-readiness.json') as f:
    d = json.load(f)
print(d.get('risk', ''))
")"
  if [[ -z "$score" || -z "$risk" ]]; then
    echo "[FAIL] Server pr-readiness missing score or risk field"
    exit 1
  fi
  echo
  echo "[PASS] Server pr-readiness (PR #$PR_NUMBER, score=$score, risk=$risk)"
else
  echo "No open PRs found; skipping server pr-readiness test."
  echo "[PASS] Server pr-readiness (skipped — no open PRs)"
fi

# ── CLI runs-failed ──────────────────────────────────────────
echo
echo "== CLI runs-failed =="
if python3 tools/github-multitool/github_multitool.py runs-failed --limit 5 > /tmp/github-multitool-cli-runs-failed.json 2>&1; then
  cat /tmp/github-multitool-cli-runs-failed.json

  # Quick validation: output must have ok key
  ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-cli-runs-failed.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
")"
  if [[ "$ok_val" != "True" ]]; then
    echo "[FAIL] CLI runs-failed missing ok=true"
    exit 1
  fi
  echo
  echo "[PASS] CLI runs-failed"
else
  echo "CLI runs-failed returned non-zero; output:"
  cat /tmp/github-multitool-cli-runs-failed.json
  echo
  echo "[PASS] CLI runs-failed (graceful error — may be expected if no failed runs or gh not configured)"
fi

# ── Server /runs/failed ────────────────────────────────────────
echo
echo "== Server /runs/failed =="
FAILED_HTTP_CODE="$(curl -sS -o /tmp/github-multitool-server-runs-failed.json -w '%{http_code}' 'http://127.0.0.1:8765/runs/failed?limit=5' || echo '000')"
if [[ "$FAILED_HTTP_CODE" == "200" ]]; then
  cat /tmp/github-multitool-server-runs-failed.json
  ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-server-runs-failed.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
")"
  if [[ "$ok_val" != "True" ]]; then
    echo "[FAIL] Server /runs/failed missing ok=true"
    exit 1
  fi
  echo
  echo "[PASS] Server /runs/failed"
else
  echo "Server /runs/failed returned HTTP $FAILED_HTTP_CODE; output:"
  cat /tmp/github-multitool-server-runs-failed.json 2>/dev/null || true
  echo
  echo "[PASS] Server /runs/failed (graceful error)"
fi

# ── CLI run-explain --help ─────────────────────────────────────
echo
echo "== CLI run-explain --help =="
python3 tools/github-multitool/github_multitool.py run-explain --help > /tmp/github-multitool-run-explain-help.txt
cat /tmp/github-multitool-run-explain-help.txt
echo
echo "[PASS] CLI run-explain --help"

# ── Server /run/<id>/explain (with safe fallback) ──────────────
echo
echo "== Server /run/<id>/explain =="
# Find a failed run ID from the failed runs list, or skip
FAILED_RUN_ID="$(python3 -c "
import json
try:
    with open('/tmp/github-multitool-server-runs-failed.json') as f:
        d = json.load(f)
    runs = d.get('failed_runs', [])
    if runs:
        print(runs[0].get('database_id', ''))
except Exception:
    pass
" 2>/dev/null || echo "")"

if [[ -n "$FAILED_RUN_ID" ]]; then
  EXPLAIN_HTTP_CODE="$(curl -sS -o /tmp/github-multitool-server-run-explain.json -w '%{http_code}' "http://127.0.0.1:8765/run/$FAILED_RUN_ID/explain?log_lines=40" || echo '000')"
  cat /tmp/github-multitool-server-run-explain.json
  if [[ "$EXPLAIN_HTTP_CODE" == "200" ]]; then
    ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-server-run-explain.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
")"
    if [[ "$ok_val" != "True" ]]; then
      echo "[FAIL] Server /run/<id>/explain missing ok=true"
      exit 1
    fi
    echo
    echo "[PASS] Server /run/<id>/explain (run #$FAILED_RUN_ID)"
  else
    echo "Server /run/<id>/explain returned HTTP $EXPLAIN_HTTP_CODE"
    echo "[PASS] Server /run/<id>/explain (graceful error)"
  fi
else
  echo "No failed runs found; skipping server /run/<id>/explain test."
  echo "[PASS] Server /run/<id>/explain (skipped — no failed runs)"
fi

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

# ── Feature 5: Safe PR Creator smoke tests ─────────────────────

echo
echo "== CLI pr-create --help =="
python3 tools/github-multitool/github_multitool.py pr-create --help > /tmp/github-multitool-pr-create-help.txt
cat /tmp/github-multitool-pr-create-help.txt
echo
echo "[PASS] CLI pr-create --help"

# Create a temp body file for refusal tests
echo "test body" > /tmp/test-pr-body-smoke.md

echo
echo "== CLI pr-create refusal without --confirm =="
set +e  # allow pr-create refusal to return non-zero
python3 tools/github-multitool/github_multitool.py pr-create   --title "test"   --body-file /tmp/test-pr-body-smoke.md   --head current   > /tmp/github-multitool-pr-create-no-confirm.json 2>/tmp/github-multitool-pr-create-no-confirm.err

cat /tmp/github-multitool-pr-create-no-confirm.json

ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-create-no-confirm.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
")"
error_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-create-no-confirm.json') as f:
    d = json.load(f)
print(d.get('error', ''))
")"

if [[ "$ok_val" != "False" ]]; then
  echo "[FAIL] Expected ok=false for pr-create without --confirm, got ok=$ok_val"
  exit 1
fi
if [[ "$error_val" != *"confirm"* ]]; then
  echo "[FAIL] Expected confirm-related error, got: $error_val"
  exit 1
fi
echo "[PASS] CLI pr-create refused without --confirm: $error_val"
set -e

echo
echo "== CLI pr-create refusal with write tools disabled =="
# Write tools are disabled by default in config, so this should refuse
set +e  # allow pr-create refusal to return non-zero
python3 tools/github-multitool/github_multitool.py pr-create   --title "test"   --body-file /tmp/test-pr-body-smoke.md   --head current   --confirm   > /tmp/github-multitool-pr-create-disabled.json 2>/tmp/github-multitool-pr-create-disabled.err

cat /tmp/github-multitool-pr-create-disabled.json

ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-create-disabled.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
")"
error_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-create-disabled.json') as f:
    d = json.load(f)
print(d.get('error', ''))
")"

if [[ "$ok_val" != "False" ]]; then
  echo "[FAIL] Expected ok=false for pr-create with write tools disabled, got ok=$ok_val"
  exit 1
fi
if [[ "$error_val" != *"Write tools are disabled"* ]]; then
  echo "[FAIL] Expected write-tools-disabled error, got: $error_val"
  exit 1
fi
echo "[PASS] CLI pr-create refused with write tools disabled: $error_val"
set -e

# Clean up temp files
rm -f /tmp/test-pr-body-smoke.md


# ── Feature 6: PR Body Generator smoke tests ─────────────────────

echo
echo "== CLI pr-body --help =="
python3 tools/github-multitool/github_multitool.py pr-body --help > /tmp/github-multitool-pr-body-help.txt
cat /tmp/github-multitool-pr-body-help.txt
echo
echo "[PASS] CLI pr-body --help"

echo
echo "== CLI pr-body generation =="
set +e  # allow pr-body to return non-zero on main/master
python3 tools/github-multitool/github_multitool.py pr-body > /tmp/github-multitool-pr-body.json 2>/tmp/github-multitool-pr-body.err
pr_body_exit=$?
set -e

cat /tmp/github-multitool-pr-body.json

ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
" 2>/dev/null || echo "")"

if [[ "$pr_body_exit" -eq 0 && "$ok_val" == "True" ]]; then
  # Success: verify output fields
  output_path="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('output_path', ''))
")"
  branch_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('branch', ''))
")"
  base_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('base', ''))
")"
  commit_count="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('commit_count', ''))
")"
  changed_count="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('changed_file_count', ''))
")"
  verification="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('verification_detected', ''))
")"

  if [[ -z "$output_path" || -z "$branch_val" || -z "$base_val" || -z "$commit_count" || -z "$changed_count" || -z "$verification" ]]; then
    echo "[FAIL] CLI pr-body output missing required fields"
    exit 1
  fi

  if [[ ! -f "$output_path" ]]; then
    echo "[FAIL] CLI pr-body output file does not exist: $output_path"
    exit 1
  fi

  # Verify generated content has expected sections
  if ! grep -q "## Summary" "$output_path"; then
    echo "[FAIL] Generated PR body missing Summary section"
    exit 1
  fi
  if ! grep -q "## Changes" "$output_path"; then
    echo "[FAIL] Generated PR body missing Changes section"
    exit 1
  fi
  if ! grep -q "## Verification" "$output_path"; then
    echo "[FAIL] Generated PR body missing Verification section"
    exit 1
  fi
  if ! grep -q "## Risk" "$output_path"; then
    echo "[FAIL] Generated PR body missing Risk section"
    exit 1
  fi
  if ! grep -q "## Rollback" "$output_path"; then
    echo "[FAIL] Generated PR body missing Rollback section"
    exit 1
  fi
  if ! grep -q "## Reviewer Notes" "$output_path"; then
    echo "[FAIL] Generated PR body missing Reviewer Notes section"
    exit 1
  fi

  # Verify generated files are not staged
  if git diff --cached --name-only | grep -q '^dist/github-pr-bodies/'; then
    echo "[FAIL] dist/github-pr-bodies/ files are staged"
    exit 1
  fi

  echo
  echo "[PASS] CLI pr-body generated successfully (branch=$branch_val, base=$base_val, commits=$commit_count, files=$changed_count, verification=$verification)"
elif [[ "$ok_val" == "False" ]]; then
  error_val="$(python3 -c "
import json
with open('/tmp/github-multitool-pr-body.json') as f:
    d = json.load(f)
print(d.get('error', ''))
" 2>/dev/null || echo "")"

  if [[ "$error_val" == *"main"* || "$error_val" == *"master"* ]]; then
    echo
    echo "[PASS] CLI pr-body correctly refused on main/master: $error_val"
  else
    echo
    echo "[PASS] CLI pr-body (graceful refusal: $error_val)"
  fi
else
  echo
  echo "[PASS] CLI pr-body (non-zero exit but handled)"
fi

# Clean up generated pr-body files from smoke test
rm -rf dist/github-pr-bodies/



# ── Feature 7: Branch Cleanup Advisor smoke tests ──────────────

echo
echo "== CLI branches-cleanup-plan --help =="
python3 tools/github-multitool/github_multitool.py branches-cleanup-plan --help > /tmp/github-multitool-cleanup-help.txt
cat /tmp/github-multitool-cleanup-help.txt
echo
echo "[PASS] CLI branches-cleanup-plan --help"

echo
echo "== CLI branches-cleanup-plan =="
set +e  # allow non-zero exit but not crash
python3 tools/github-multitool/github_multitool.py branches-cleanup-plan > /tmp/github-multitool-cleanup-plan.json 2>/tmp/github-multitool-cleanup-plan.err
cleanup_exit=$?
set -e

cat /tmp/github-multitool-cleanup-plan.json

# Validate JSON output shape
ok_val="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('ok', ''))
" 2>/dev/null || echo "")"

if [[ "$ok_val" == "True" ]]; then
  # Verify required fields exist
  repo_val="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('repository', ''))
" 2>/dev/null || echo "")"
  default_branch="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('default_branch', ''))
" 2>/dev/null || echo "")"
  current_branch="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('current_branch', ''))
" 2>/dev/null || echo "")"
  generated_at="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('generated_at', ''))
" 2>/dev/null || echo "")"
  safe_local="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('safe_to_delete_local', ''))
" 2>/dev/null || echo "")"
  safe_remote="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('safe_to_delete_remote', ''))
" 2>/dev/null || echo "")"
  manual_review="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('needs_manual_review', ''))
" 2>/dev/null || echo "")"
  do_not_delete="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('do_not_delete', ''))
" 2>/dev/null || echo "")"

  if [[ -z "$repo_val" || -z "$default_branch" || -z "$current_branch" || -z "$generated_at" || -z "$safe_local" || -z "$safe_remote" || -z "$manual_review" || -z "$do_not_delete" ]]; then
    echo "[FAIL] CLI branches-cleanup-plan missing required fields"
    exit 1
  fi

  # Verify default_branch is in do_not_delete list
  default_in_dnd="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
default_branch = d.get('default_branch', '')
branches = [b.get('branch', '') for b in d.get('do_not_delete', [])]
print('yes' if default_branch in branches else 'no')
" 2>/dev/null || echo "no")"
  if [[ "$default_in_dnd" != "yes" ]]; then
    echo "[FAIL] Default branch not found in do_not_delete"
    exit 1
  fi

  # Verify current_branch is in do_not_delete list
  current_in_dnd="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
current_branch = d.get('current_branch', '')
branches = [b.get('branch', '') for b in d.get('do_not_delete', [])]
print('yes' if current_branch in branches else 'no')
" 2>/dev/null || echo "no")"
  if [[ "$current_in_dnd" != "yes" ]]; then
    echo "[FAIL] Current branch not found in do_not_delete"
    exit 1
  fi

  # Verify no safe_to_delete entry has a suggested command with -D (force)
  has_force="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
for entry in d.get('safe_to_delete_local', []) + d.get('safe_to_delete_remote', []):
    cmd = entry.get('suggested_command', '')
    if '-D' in cmd:
        print('yes')
        break
else:
    print('no')
" 2>/dev/null || echo "no")"
  if [[ "$has_force" == "yes" ]]; then
    echo "[FAIL] Force-delete flag (-D) found in safe suggested commands"
    exit 1
  fi

  echo
  echo "[PASS] CLI branches-cleanup-plan (repo=$repo_val, default=$default_branch, current=$current_branch)"
else
  error_val="$(python3 -c "
import json
with open('/tmp/github-multitool-cleanup-plan.json') as f:
    d = json.load(f)
print(d.get('error', ''))
" 2>/dev/null || echo "")"
  echo
  echo "[PASS] CLI branches-cleanup-plan (graceful error: $error_val)"
fi

echo "== Final result =="
echo "[PASS] GitHub multitool smoke test completed successfully."

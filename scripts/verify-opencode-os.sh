#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

failures=0

check() {
  local label="$1"
  shift

  if "$@"; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"
    failures=$((failures + 1))
  fi
}

echo "== Verify Calvin opencode OS =="

echo
echo "== Required files =="
check "README.md exists" test -f README.md
check "AGENTS.md exists" test -f AGENTS.md
check ".gitignore exists" test -f .gitignore
check ".env.example exists" test -f .env.example
check ".env is absent" test ! -f .env
check "opencode config exists" test -f .opencode/opencode.json
check "agent registry exists" test -f registries/agent-registry.md
check "command registry exists" test -f registries/command-registry.md
check "skill registry exists" test -f registries/skill-registry.md
check "project memory exists" test -f docs/project-memory.md

echo
echo "== Shell syntax =="
for script in scripts/*.sh; do
  [[ -f "$script" ]] || continue
  check "bash -n $script" bash -n "$script"
done

echo
echo "== Registry coverage =="

while IFS= read -r file; do
  name="$(basename "$file" .md)"
  check "agent registered: $name" grep -qF "$file" registries/agent-registry.md
done < <(find .opencode/agents -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  name="$(basename "$file" .md)"
  check "command registered: $name" grep -qF "$file" registries/command-registry.md
done < <(find .opencode/commands -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  skill_dir="$(basename "$(dirname "$file")")"
  check "skill registered: $skill_dir" grep -qF "$file" registries/skill-registry.md
done < <(find .opencode/skills -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | sort)

echo
echo "== Generated files staging check =="
if git diff --cached --name-only | grep -q '^dist/'; then
  echo "[FAIL] dist files are staged"
  failures=$((failures + 1))
else
  echo "[PASS] no dist files staged"
fi

echo
echo "== Context pack generation =="
if ./scripts/build-context-pack.sh >/tmp/opencode-os-context-pack-check.log 2>&1; then
  echo "[PASS] context pack generation"
else
  echo "[FAIL] context pack generation"
  cat /tmp/opencode-os-context-pack-check.log
  failures=$((failures + 1))
fi

echo
echo "== Final result =="

if (( failures > 0 )); then
  echo "[FAIL] Verification completed with $failures failure(s)."
  exit 1
fi

echo "[PASS] Verification completed successfully."

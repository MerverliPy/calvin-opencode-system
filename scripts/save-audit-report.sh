#!/usr/bin/env bash
set -Eeuo pipefail

COMMIT=0
PUSH=0
FROM_STDIN=0
FROM_CLIPBOARD=0
SOURCE_FILE=""

usage() {
  cat <<'HELP_EOF'
Usage:
  ./scripts/save-audit-report.sh path/to/audit-response.md [--commit] [--push]
  ./scripts/save-audit-report.sh --stdin [--commit] [--push]
  ./scripts/save-audit-report.sh --clipboard [--commit] [--push]

Options:
  --commit      Commit the saved audit report.
  --push        Push the commit to origin/current-branch.
  --stdin       Read audit markdown from standard input.
  --clipboard   Read audit markdown from Windows clipboard if available.
  -h, --help    Show this help.

Examples:
  ./scripts/save-audit-report.sh ~/Downloads/audit-response.md --commit --push

  cat ~/Downloads/audit-response.md | ./scripts/save-audit-report.sh --stdin --commit --push
HELP_EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit)
      COMMIT=1
      shift
      ;;
    --push)
      PUSH=1
      COMMIT=1
      shift
      ;;
    --stdin)
      FROM_STDIN=1
      shift
      ;;
    --clipboard)
      FROM_CLIPBOARD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$SOURCE_FILE" ]]; then
        SOURCE_FILE="$1"
        shift
      else
        echo "Unknown extra argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

input_modes=0
[[ -n "$SOURCE_FILE" ]] && input_modes=$((input_modes + 1))
[[ "$FROM_STDIN" -eq 1 ]] && input_modes=$((input_modes + 1))
[[ "$FROM_CLIPBOARD" -eq 1 ]] && input_modes=$((input_modes + 1))

if [[ "$input_modes" -ne 1 ]]; then
  echo "ERROR: Provide exactly one input source: file path, --stdin, or --clipboard." >&2
  usage >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

TMP_INPUT="$(mktemp)"
trap 'rm -f "$TMP_INPUT"' EXIT

if [[ -n "$SOURCE_FILE" ]]; then
  if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "ERROR: Audit response file not found: $SOURCE_FILE" >&2
    exit 1
  fi
  cp "$SOURCE_FILE" "$TMP_INPUT"
elif [[ "$FROM_STDIN" -eq 1 ]]; then
  cat > "$TMP_INPUT"
elif [[ "$FROM_CLIPBOARD" -eq 1 ]]; then
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "Get-Clipboard" > "$TMP_INPUT"
  else
    echo "ERROR: powershell.exe is not available for clipboard import." >&2
    exit 1
  fi
fi

if [[ ! -s "$TMP_INPUT" ]]; then
  echo "ERROR: Audit input is empty." >&2
  exit 1
fi

AUDIT_DIR="$REPO_ROOT/docs/audits"
mkdir -p "$AUDIT_DIR"

max_num="$(
  find "$AUDIT_DIR" -maxdepth 1 -type f -name 'opencode-system-audit-[0-9][0-9][0-9].md' 2>/dev/null \
    | sed -E 's/.*opencode-system-audit-([0-9]{3})\.md/\1/' \
    | sort -n \
    | tail -1
)"

if [[ -z "$max_num" ]]; then
  next_num=1
else
  next_num=$((10#$max_num + 1))
fi

audit_id="$(printf '%03d' "$next_num")"
OUTFILE="$AUDIT_DIR/opencode-system-audit-$audit_id.md"
README="$AUDIT_DIR/README.md"
timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
branch="$(git branch --show-current 2>/dev/null || echo unknown)"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

{
  echo "# opencode System Audit $audit_id"
  echo
  echo "Saved: $timestamp"
  echo
  echo "Repository branch: $branch"
  echo
  echo "Repository commit at save time: $commit"
  echo
  echo "Source: ${SOURCE_FILE:-stdin-or-clipboard}"
  echo
  echo "---"
  echo
  cat "$TMP_INPUT"
} > "$OUTFILE"

if [[ ! -f "$README" ]]; then
  cat > "$README" <<'README_EOF'
# opencode System Audits

This folder stores repository audit reports for Calvin's private opencode operating system.

| Audit | File | Saved |
|---|---|---|
README_EOF
fi

if ! grep -qF "opencode-system-audit-$audit_id.md" "$README"; then
  printf '| %s | `%s` | %s |\n' "$audit_id" "docs/audits/opencode-system-audit-$audit_id.md" "$timestamp" >> "$README"
fi

echo "== Saved audit report =="
echo "$OUTFILE"

git add "$OUTFILE" "$README"
git restore --staged dist/context-packs 2>/dev/null || true
git restore --staged dist/audit-requests 2>/dev/null || true

echo
echo "== Staged files =="
git diff --cached --name-only

if [[ "$COMMIT" -eq 1 ]]; then
  if git diff --cached --quiet; then
    echo "No staged audit changes to commit."
  else
    git commit -m "Add opencode system audit $audit_id"
  fi
fi

if [[ "$PUSH" -eq 1 ]]; then
  current_branch="$(git branch --show-current)"
  git push origin "$current_branch"
fi

echo
echo "== Git status =="
git status --short

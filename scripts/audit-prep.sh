#!/usr/bin/env bash
set -Eeuo pipefail

PULL=1
COPY_TO_WINDOWS_DOWNLOADS=0
COPY_TO_CLIPBOARD=0
PRINT_PROMPT=0

for arg in "$@"; do
  case "$arg" in
    --no-pull)
      PULL=0
      ;;
    --windows-copy)
      COPY_TO_WINDOWS_DOWNLOADS=1
      ;;
    --no-windows-copy)
      COPY_TO_WINDOWS_DOWNLOADS=0
      ;;
    --clipboard)
      COPY_TO_CLIPBOARD=1
      ;;
    --print-prompt)
      PRINT_PROMPT=1
      ;;
    -h|--help)
      cat <<'HELP_EOF'
Usage:
  ./scripts/audit-prep.sh [options]

Options:
  --no-pull            Do not run git pull before preparing audit files.
  --windows-copy       Copy output files to Windows Downloads if available.
  --no-windows-copy    Explicitly disable Windows Downloads copy.
  --clipboard          Copy the audit prompt to the Windows clipboard if available.
  --print-prompt       Print the audit prompt to terminal.
  -h, --help           Show this help.

Termius / iPhone default:
  No Windows clipboard.
  No Windows Downloads copy.
  Use Termius SFTP to download:
    dist/audit-requests/opencode-audit-upload.md

Outputs:
  dist/context-packs/calvin-opencode-system-context-pack.md
  dist/audit-requests/audit-request.md
  dist/audit-requests/opencode-audit-upload.md
  dist/audit-requests/sensitive-warning-report.txt
  dist/audit-requests/mobile-upload-instructions.txt
HELP_EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

if [[ ! -x scripts/build-context-pack.sh ]]; then
  echo "ERROR: scripts/build-context-pack.sh is missing or not executable." >&2
  exit 1
fi

current_branch="$(git branch --show-current 2>/dev/null || echo unknown)"

if [[ "$PULL" -eq 1 ]]; then
  if [[ "$current_branch" == "main" ]]; then
    echo "== Pull latest main =="
    git pull --ff-only origin main
  else
    echo "== Skipping pull because current branch is not main: $current_branch =="
  fi
fi

echo "== Build context pack =="
./scripts/build-context-pack.sh

CONTEXT_PACK="$REPO_ROOT/dist/context-packs/calvin-opencode-system-context-pack.md"
AUDIT_DIR="$REPO_ROOT/dist/audit-requests"
PROMPT_FILE="$AUDIT_DIR/audit-request.md"
UPLOAD_FILE="$AUDIT_DIR/opencode-audit-upload.md"
WARNING_FILE="$AUDIT_DIR/sensitive-warning-report.txt"
INSTRUCTIONS_FILE="$AUDIT_DIR/mobile-upload-instructions.txt"

mkdir -p "$AUDIT_DIR"

if [[ ! -f "$CONTEXT_PACK" ]]; then
  echo "ERROR: Context pack was not created: $CONTEXT_PACK" >&2
  exit 1
fi

echo "== Extract sensitive warning section =="
awk '
  /## Sensitive Pattern Warning Report/ {flag=1}
  /## Git Status Summary/ {if (flag) exit}
  flag {print}
' "$CONTEXT_PACK" > "$WARNING_FILE"

warning_count="$(grep -c '^- ' "$WARNING_FILE" 2>/dev/null || true)"

cat > "$PROMPT_FILE" <<'PROMPT_EOF'
Analyze the attached repository context pack using the repository audit workflow and audit template included inside the context pack.

Produce a complete Repository Audit Report for my private opencode operating system repository.

Focus on:

1. repository structure
2. .opencode agents, commands, and skills
3. reusable workflow templates
4. registries
5. documentation clarity
6. local model routing assumptions
7. security hygiene
8. missing automation
9. opportunities for new agents, commands, skills, and integrations

Separate confirmed findings from assumptions.

Do not reveal or repeat any secret values if found.

Return this structure:

# Repository Audit Report

## Executive Summary

## Current Strengths

## Critical Issues

## Quick Wins

## Structural Recommendations

## opencode Agent Review

## opencode Command Review

## opencode Skill Review

## Security and Hygiene Review

## Documentation Review

## Recommended New Files

Use this table:

| File | Purpose | Priority |
|---|---|---|

## Prioritized Execution Plan

## Clarification Defaults

Use short options and highlight the recommended answer.
PROMPT_EOF

{
  echo "# Calvin opencode OS Audit Upload Package"
  echo
  echo "## How to use this file"
  echo
  echo "Upload this single Markdown file into ChatGPT or opencode and ask it to follow the audit request below."
  echo
  echo "This file contains:"
  echo
  echo "1. the audit request"
  echo "2. the generated repository context pack"
  echo
  echo "---"
  echo
  echo "# Audit Request"
  echo
  cat "$PROMPT_FILE"
  echo
  echo "---"
  echo
  echo "# Repository Context Pack"
  echo
  cat "$CONTEXT_PACK"
} > "$UPLOAD_FILE"

cat > "$INSTRUCTIONS_FILE" <<INSTRUCTIONS_EOF
Termius / iPhone workflow:

1. Use Termius SFTP or file browser to download this one file:
   $UPLOAD_FILE

2. Upload that Markdown file into ChatGPT.

3. Use this prompt:
   Analyze the attached audit upload package and produce the requested Repository Audit Report.

4. Save the AI response as a Markdown file.

5. Upload that response back to WSL2 or place it somewhere accessible.

6. Run:
   ./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push

Important files:

Combined upload file:
  $UPLOAD_FILE

Prompt only:
  $PROMPT_FILE

Context pack only:
  $CONTEXT_PACK

Sensitive warning report:
  $WARNING_FILE

Sensitive warning count:
  $warning_count

Optional desktop-only helpers:

Copy files to Windows Downloads:
  ./scripts/opencode-os.sh audit-prep --windows-copy

Copy prompt to Windows clipboard:
  ./scripts/opencode-os.sh audit-prep --clipboard
INSTRUCTIONS_EOF

copied_to_windows="no"
clipboard_status="not requested"

if [[ "$COPY_TO_WINDOWS_DOWNLOADS" -eq 1 && -d /mnt/c/Users ]]; then
  while IFS= read -r downloads_dir; do
    if [[ -d "$downloads_dir" && -w "$downloads_dir" ]]; then
      cp "$UPLOAD_FILE" "$downloads_dir/calvin-opencode-audit-upload.md"
      cp "$PROMPT_FILE" "$downloads_dir/calvin-opencode-audit-request.md"
      cp "$INSTRUCTIONS_FILE" "$downloads_dir/calvin-opencode-mobile-upload-instructions.txt"
      copied_to_windows="yes: $downloads_dir"
      break
    fi
  done < <(find /mnt/c/Users -maxdepth 2 -type d -name Downloads 2>/dev/null | sort)
fi

if [[ "$COPY_TO_CLIPBOARD" -eq 1 ]]; then
  clipboard_status="requested but unavailable"
  if command -v clip.exe >/dev/null 2>&1; then
    if clip.exe < "$PROMPT_FILE" 2>/dev/null; then
      clipboard_status="copied with clip.exe"
    fi
  elif [[ -x /mnt/c/Windows/System32/clip.exe ]]; then
    if /mnt/c/Windows/System32/clip.exe < "$PROMPT_FILE" 2>/dev/null; then
      clipboard_status="copied with /mnt/c/Windows/System32/clip.exe"
    fi
  fi
fi

upload_size="$(du -h "$UPLOAD_FILE" | awk '{print $1}')"
context_size="$(du -h "$CONTEXT_PACK" | awk '{print $1}')"

echo
echo "== Audit prep complete =="
echo
echo "Combined upload file:"
echo "  $UPLOAD_FILE"
echo
echo "Context pack:"
echo "  $CONTEXT_PACK"
echo
echo "Audit prompt:"
echo "  $PROMPT_FILE"
echo
echo "Mobile instructions:"
echo "  $INSTRUCTIONS_FILE"
echo
echo "Sensitive warning report:"
echo "  $WARNING_FILE"
echo
echo "Sensitive warning count:"
echo "  $warning_count"
echo
echo "Combined upload file size:"
echo "  $upload_size"
echo
echo "Context pack size:"
echo "  $context_size"
echo
echo "Copied to Windows Downloads:"
echo "  $copied_to_windows"
echo
echo "Clipboard:"
echo "  $clipboard_status"
echo

if [[ "$PRINT_PROMPT" -eq 1 ]]; then
  echo "== Audit prompt =="
  cat "$PROMPT_FILE"
fi

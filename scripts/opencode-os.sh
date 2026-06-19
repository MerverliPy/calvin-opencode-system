#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

cmd="${1:-help}"
shift || true

case "$cmd" in
  context-pack|context)
    ./scripts/build-context-pack.sh "$@"
    ;;

  audit-prep|prep-audit|prep)
    ./scripts/audit-prep.sh "$@"
    ;;

  save-audit)
    ./scripts/save-audit-report.sh "$@"
    ;;

  status)
    echo "== Repo =="
    pwd
    echo
    echo "== Branch =="
    git branch --show-current
    echo
    echo "== Git status =="
    git status --short
    echo
    echo "== Recent commits =="
    git log --oneline -5
    echo
    echo "== Generated audit files =="
    find dist/audit-requests -maxdepth 1 -type f 2>/dev/null | sort || true
    echo
    echo "== Saved audits =="
    find docs/audits -maxdepth 1 -type f -name 'opencode-system-audit-*.md' 2>/dev/null | sort || true
    ;;

  help|-h|--help)
    cat <<'HELP_EOF'
Calvin opencode OS command router

Usage:
  ./scripts/opencode-os.sh context-pack
  ./scripts/opencode-os.sh audit-prep
  ./scripts/opencode-os.sh audit-prep --no-pull
  ./scripts/opencode-os.sh audit-prep --print-prompt
  ./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push
  ./scripts/opencode-os.sh save-audit --stdin --commit --push
  ./scripts/opencode-os.sh save-audit --clipboard --commit --push
  ./scripts/opencode-os.sh status

Recommended Termius/iPhone workflow:
  1. ./scripts/opencode-os.sh audit-prep
  2. Download dist/audit-requests/opencode-audit-upload.md through Termius SFTP.
  3. Upload that one Markdown file into ChatGPT.
  4. Save the ChatGPT audit response as a Markdown file.
  5. Upload the response back to WSL2.
  6. ./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push
HELP_EOF
    ;;

  *)
    echo "Unknown command: $cmd" >&2
    echo "Run: ./scripts/opencode-os.sh help" >&2
    exit 2
    ;;
esac

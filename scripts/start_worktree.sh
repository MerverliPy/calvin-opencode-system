#!/usr/bin/env bash
set -euo pipefail

TASK="${1:-agent-task}"
ROOT="$(git rev-parse --show-toplevel)"
REPO="$(basename "$ROOT")"
TARGET="../${REPO}-${TASK}"

git worktree add "$TARGET" -b "ai/${TASK}"
echo "Created worktree: $TARGET"
echo "Next:"
echo "  cd $TARGET"
echo "  opencode"

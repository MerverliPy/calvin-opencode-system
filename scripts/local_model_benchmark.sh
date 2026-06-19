#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-qwen2.5-coder:7b}"
PROMPT="${2:-Explain this machine's best local coding model role for opencode in 10 bullets.}"

echo "== Testing Ollama model: $MODEL =="
ollama run "$MODEL" "$PROMPT"

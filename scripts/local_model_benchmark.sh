#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-qwen2.5-coder:7b}"

if [[ $# -ge 2 ]]; then
  PROMPT="$2"
else
  PROMPT="Explain this machine best local coding model role for opencode in 10 bullets."
fi

echo "== Testing Ollama model: $MODEL =="
ollama run "$MODEL" "$PROMPT"

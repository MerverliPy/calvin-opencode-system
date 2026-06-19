#!/usr/bin/env bash
set -euo pipefail

echo "== Calvin opencode WSL2 setup =="

sudo apt update
sudo apt install -y \
  curl wget git jq ripgrep fd-find build-essential ca-certificates gnupg lsb-release unzip \
  python3 python3-pip python3-venv \
  nodejs npm

echo "== Install opencode =="
curl -fsSL https://opencode.ai/install | bash || true

echo "== Install Ollama =="
curl -fsSL https://ollama.com/install.sh | sh || true

echo "== Suggested local models =="
cat <<'MODELS'
Recommended pulls for RTX 4070 12GB:
  ollama pull qwen2.5-coder:7b
  ollama pull qwen2.5-coder:14b
  ollama pull qwen2.5-coder:3b
Then configure context manually if needed.
MODELS

echo "== Verify =="
which opencode || true
which ollama || true
nvidia-smi || true

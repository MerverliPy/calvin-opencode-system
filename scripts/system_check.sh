#!/usr/bin/env bash
set -euo pipefail

echo "== OS =="
uname -a || true

echo "== WSL =="
grep -i microsoft /proc/version || true

echo "== GPU =="
nvidia-smi || true

echo "== CPU =="
lscpu | sed -n '1,25p' || true

echo "== Memory =="
free -h || true

echo "== Disk =="
df -h | sed -n '1,20p' || true

echo "== Tools =="
for cmd in git node npm python3 docker opencode ollama; do
  printf "%-12s" "$cmd"
  command -v "$cmd" || true
done

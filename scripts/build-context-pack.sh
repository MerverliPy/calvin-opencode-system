#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OUTPUT_DIR="$REPO_ROOT/dist/context-packs"
OUTPUT_FILE="$OUTPUT_DIR/calvin-opencode-system-context-pack.md"
MAX_FILE_BYTES="${MAX_FILE_BYTES:-1048576}"

SENSITIVE_REGEX='(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PRIVATE[[:space:]_-]?KEY|BEGIN [A-Z ]*PRIVATE KEY)'

mkdir -p "$OUTPUT_DIR"
cd "$REPO_ROOT"

branch="$(git branch --show-current 2>/dev/null || echo 'unknown')"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

INCLUDE_PATHS=(
  "README.md"
  "README_MASTER_GUIDE.md"
  "AGENTS.md"
  ".opencode"
  "docs"
  "templates"
  "registries"
  "configs"
  "scripts"
  ".env.example"
  ".gitignore"
)

is_excluded() {
  local path="$1"
  local base
  base="$(basename "$path")"

  case "$path" in
    ./.git/*|.git/*|*/.git/*) return 0 ;;
    ./node_modules/*|node_modules/*|*/node_modules/*) return 0 ;;
    ./dist/*|dist/*|*/dist/*) return 0 ;;
    ./build/*|build/*|*/build/*) return 0 ;;
    ./coverage/*|coverage/*|*/coverage/*) return 0 ;;
    ./.cache/*|.cache/*|*/.cache/*) return 0 ;;
    ./tmp/*|tmp/*|*/tmp/*) return 0 ;;
    ./models/*|models/*|*/models/*) return 0 ;;
    ./ollama-models/*|ollama-models/*|*/ollama-models/*) return 0 ;;
    ./lmstudio-models/*|lmstudio-models/*|*/lmstudio-models/*) return 0 ;;
    ./secrets/*|secrets/*|*/secrets/*) return 0 ;;
    ./tokens/*|tokens/*|*/tokens/*) return 0 ;;
    ./credentials/*|credentials/*|*/credentials/*) return 0 ;;
  esac

  case "$base" in
    .env|.env.*|*.log|*.gguf|*.safetensors|*.bin) return 0 ;;
  esac

  return 1
}

is_binary() {
  local file="$1"

  if command -v file >/dev/null 2>&1; then
    file --mime "$file" | grep -qE 'charset=binary|application/octet-stream'
  else
    ! grep -Iq . "$file" >/dev/null 2>&1
  fi
}

sanitized_git_status() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "git status unavailable"
    return 0
  fi

  local printed=0

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue

    local path="${line:3}"
    path="${path##* -> }"

    if ! is_excluded "$path"; then
      echo "$line"
      printed=1
    fi
  done < <(git status --short 2>/dev/null || true)

  if [[ "$printed" -eq 0 ]]; then
    echo "No included-path changes detected."
  fi
}

collect_files() {
  for path in "${INCLUDE_PATHS[@]}"; do
    [[ -e "$path" ]] || continue

    if [[ -f "$path" ]]; then
      if ! is_excluded "$path"; then
        printf '%s\n' "$path"
      fi
      continue
    fi

    if [[ -d "$path" ]]; then
      find "$path" -type f | while read -r file; do
        if ! is_excluded "$file"; then
          printf '%s\n' "$file"
        fi
      done
    fi
  done | sed 's#^./##' | sort -u
}

scan_sensitive_patterns() {
  local file
  local count=0

  if [[ -z "${file_list:-}" ]]; then
    echo "No files available for sensitive-pattern scanning."
    return 0
  fi

  while IFS= read -r file; do
    [[ -n "$file" ]] || continue
    [[ -f "$file" ]] || continue

    case "$file" in
      scripts/build-context-pack.sh)
        continue
        ;;
    esac

    if is_binary "$file"; then
      continue
    fi

    local size
    size="$(wc -c < "$file" | tr -d ' ')"

    if (( size > MAX_FILE_BYTES )); then
      continue
    fi

    while IFS= read -r match; do
      [[ -n "$match" ]] || continue
      echo "- $match"
      count=$((count + 1))
    done < <(grep -nEI "$SENSITIVE_REGEX" "$file" 2>/dev/null | sed "s#^#$file:#" || true)
  done <<< "$file_list"

  if (( count == 0 )); then
    echo "No sensitive-pattern warnings detected."
  fi
}

file_list="$(collect_files)"
SENSITIVE_REPORT_FILE="$(mktemp)"
trap 'rm -f "$SENSITIVE_REPORT_FILE"' EXIT

scan_sensitive_patterns > "$SENSITIVE_REPORT_FILE"
sensitive_warning_count="$(awk '/^- /{c++} END{print c+0}' "$SENSITIVE_REPORT_FILE")"

{
  cat <<HEADER
# Calvin opencode System — Repository Context Pack

Generated: \`$timestamp\`  
Repository root: \`$REPO_ROOT\`  
Git branch: \`$branch\`  
Latest commit: \`$commit\`

## Purpose

This context pack is a clean, uploadable Markdown snapshot of Calvin's private opencode system repository.

## Safety Warnings

The generator intentionally excludes common secret, credential, model, dependency, cache, and build-output paths.

Excluded examples:

~~~~text
.git/
.env
.env.*
node_modules/
dist/
build/
coverage/
.cache/
tmp/
*.log
*.gguf
*.safetensors
*.bin
models/
ollama-models/
lmstudio-models/
secrets/
tokens/
credentials/
~~~~

Files larger than \`$MAX_FILE_BYTES\` bytes are skipped by default.

---

## Sensitive Pattern Warning Report

This section flags suspicious terms such as API key, secret, token, password, and private key. These warnings can be false positives when they refer to placeholder environment variable names.

~~~~text
HEADER

  cat "$SENSITIVE_REPORT_FILE"

  cat <<STATUS
~~~~

Sensitive warning count: \`$sensitive_warning_count\`

---

## Git Status Summary

~~~~text
STATUS

  sanitized_git_status

  cat <<TREE
~~~~

---

## Repository Tree Summary

~~~~text
TREE

  if command -v tree >/dev/null 2>&1; then
    tree -a -I '.git|.env|.env.*|node_modules|dist|build|coverage|.cache|tmp|*.log|*.gguf|*.safetensors|*.bin|models|ollama-models|lmstudio-models|secrets|tokens|credentials' .
  else
    find . \
      -path './.git' -prune -o \
      -name '.env' -prune -o \
      -name '.env.*' -prune -o \
      -path './node_modules' -prune -o \
      -path './dist' -prune -o \
      -path './build' -prune -o \
      -path './coverage' -prune -o \
      -path './.cache' -prune -o \
      -path './tmp' -prune -o \
      -name '*.log' -prune -o \
      -name '*.gguf' -prune -o \
      -name '*.safetensors' -prune -o \
      -name '*.bin' -prune -o \
      -path './models' -prune -o \
      -path './ollama-models' -prune -o \
      -path './lmstudio-models' -prune -o \
      -path './secrets' -prune -o \
      -path './tokens' -prune -o \
      -path './credentials' -prune -o \
      -print | sort
  fi

  cat <<LIST
~~~~

---

## Included File List

~~~~text
LIST

  if [[ -n "$file_list" ]]; then
    printf '%s\n' "$file_list"
  else
    echo "No files matched the include rules."
  fi

  cat <<CONTENTS
~~~~

---

# File Contents
CONTENTS

  if [[ -n "$file_list" ]]; then
    while IFS= read -r file; do
      [[ -n "$file" ]] || continue
      [[ -f "$file" ]] || continue

      size="$(wc -c < "$file" | tr -d ' ')"

      echo
      echo "---"
      echo
      echo "## File: \`$file\`"
      echo
      echo "Size: \`$size bytes\`"
      echo

      if (( size > MAX_FILE_BYTES )); then
        echo "> Skipped: file exceeds MAX_FILE_BYTES=$MAX_FILE_BYTES."
        continue
      fi

      if is_binary "$file"; then
        echo "> Skipped: binary or non-text file."
        continue
      fi

      echo '~~~~text'
      cat "$file"
      echo
      echo '~~~~'
    done <<< "$file_list"
  fi

  echo
  echo "---"
  echo
  echo "# End of Context Pack"
} > "$OUTPUT_FILE"

echo "Context pack created: $OUTPUT_FILE"
echo "Included files: $(printf '%s\n' "$file_list" | sed '/^$/d' | wc -l | tr -d ' ')"
echo "Max file size: $MAX_FILE_BYTES bytes"
echo "Sensitive pattern warnings: $sensitive_warning_count"

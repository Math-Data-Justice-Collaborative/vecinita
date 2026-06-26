#!/usr/bin/env bash
# Post-export verification — search target repo for Vecinita-specific leftovers.
# Usage: bash grep_vecinita_leftovers.sh /path/to/target/repo
set -euo pipefail

TARGET="${1:?Usage: $0 /path/to/target/repo}"

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: not a directory: $TARGET" >&2
  exit 2
fi

PATTERN='Vecinita|vecinita|VECINA|VECINITA|chat-rag|data-management-backend|internal-write-api|admin-fe-spec|LlamaIndex|pgvector|FastEmbed|doctl apps spec get'

echo "Scanning $TARGET for Vecinita-specific patterns..."
if rg -n --hidden -S -g '!.git' -e "$PATTERN" "$TARGET/.cursor" "$TARGET/docs" "$TARGET/workflow-state.yaml" 2>/dev/null; then
  echo ""
  echo "FAIL: matches found — sanitize before declaring export complete." >&2
  exit 1
fi

echo "OK: no Vecinita-specific pattern matches in .cursor/, docs/, workflow-state.yaml"

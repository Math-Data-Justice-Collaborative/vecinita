#!/usr/bin/env bash
# Fail if DO operator spec exports (contain EV[...] or plaintext secrets) are tracked by git.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BLOCKED=(
  admin-fe-spec.yaml
  internal-write-api-spec.yaml
  chat-rag-spec.yaml
  prod.env
  .deploy-keys.local
)

found=0
for path in "${BLOCKED[@]}"; do
  if git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    echo "ERROR: $path is tracked by git — remove with: git rm --cached $path" >&2
    found=1
  fi
done

if (( found != 0 )); then
  exit 1
fi

echo "OK: operator DO spec exports and local secret files are not tracked (see .gitignore)."

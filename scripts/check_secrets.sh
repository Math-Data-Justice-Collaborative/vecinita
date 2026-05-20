#!/usr/bin/env bash
# Fast high-confidence secret pattern scan for current tree (QA-005 / test-plan TP-006).
# CI uses this as the blocking gate; gitleaks --no-git is an optional second pass.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SCAN_DIRS=(apps packages tests infra openapi)

if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: ripgrep (rg) is required." >&2
  exit 1
fi

RG_GLOBS=(
  --glob '!**/node_modules/**'
  --glob '!**/.venv/**'
  --glob '!**/venv/**'
  --glob '!**/__pycache__/**'
  --glob '!**/dist/**'
  --glob '!**/build/**'
  --glob '!**/.pytest_cache/**'
  --glob '!**/package-lock.json'
  --glob '!**/*.min.js'
  --glob '!**/*.min.js.map'
)

# name|extended-regex (ripgrep -P)
PATTERNS=(
  'aws-access-key-id|AKIA[0-9A-Z]{16}'
  'openai-api-key|sk-(?:proj-)?[a-zA-Z0-9]{20,}'
  'github-pat|ghp_[a-zA-Z0-9]{36}'
  'github-oauth|gho_[a-zA-Z0-9]{36}'
  'github-fine-grained-pat|github_pat_[a-zA-Z0-9_]{22,}'
  'private-key-pem|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
  'stripe-live-secret|(?:sk|rk)_live_[0-9a-zA-Z]{24,}'
)

found=0
for entry in "${PATTERNS[@]}"; do
  name="${entry%%|*}"
  pattern="${entry#*|}"
  matches="$(rg -n --pcre2 "${RG_GLOBS[@]}" "$pattern" "${SCAN_DIRS[@]}" 2>/dev/null || true)"
  if [[ -n "$matches" ]]; then
    if (( found == 0 )); then
      echo "ERROR: possible secrets in current tree (pattern scan):" >&2
    fi
    echo "--- $name ---" >&2
    echo "$matches" >&2
    found=1
  fi
done

if (( found != 0 )); then
  exit 1
fi

echo "OK: no high-confidence secret patterns in ${SCAN_DIRS[*]}."

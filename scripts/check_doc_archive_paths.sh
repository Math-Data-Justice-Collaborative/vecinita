#!/usr/bin/env bash
# Fail if markdown references still point at docs/ paths moved to S000 archive.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STALE_PATTERNS=(
  'docs/execution-plan\.md'
  'docs/deploy-state\.md'
  'docs/deploy-report\.md'
  'docs/service-health-state\.md'
  'docs/data-staging-state\.md'
  'docs/qa-report\.md'
  'docs/e2e-report\.md'
  'docs/verification-report\.md'
  'docs/implementation-verification\.md'
  'docs/hotfix-log\.md'
  'docs/project-board\.md'
  'docs/audits\.md'
  'docs/context-brief\.md'
  'docs/reference\.md'
  'docs/context/'
)

# Relative links from docs/ root to moved filenames (must use sessions/S000-internal-docs-archive/)
RELATIVE_PATTERNS=(
  '\]\(execution-plan\.md\)'
  '\]\(deploy-state\.md\)'
  '\]\(context-brief\.md\)'
  '\]\(\.\./deploy-state\.md\)'
  '\]\(\.\./\.\./context/'
  '\]\(\.\./\.\./context-brief\.md\)'
  '\]\(\.\./\.\./execution-plan\.md\)'
  '\]\(\.\./\.\./project-board\.md\)'
)

fail=0
scan() {
  local label=$1
  shift
  local out
  out="$(rg -n "$@" \
    --glob '!.wiki-build/**' \
    --glob '!scripts/check_doc_archive_paths.sh' \
    --glob '!docs/sessions/S000-internal-docs-archive/session-brief.md' \
    . 2>/dev/null || true)"
  if [[ -n "$out" ]]; then
    echo "ERROR: stale $label references:" >&2
    echo "$out" >&2
    fail=1
  fi
}

for pat in "${STALE_PATTERNS[@]}"; do
  scan "absolute path ($pat)" "$pat"
done

for pat in "${RELATIVE_PATTERNS[@]}"; do
  scan "relative link ($pat)" "$pat" docs/ .cursor/
done

if [[ "$fail" -ne 0 ]]; then
  echo "Update paths to docs/sessions/S000-internal-docs-archive/ (see session-brief.md)." >&2
  exit 1
fi

echo "OK: no stale doc archive path references"

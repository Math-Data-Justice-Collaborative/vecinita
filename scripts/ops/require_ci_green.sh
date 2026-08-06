#!/usr/bin/env bash
# Require tip SHA CI green before promote/cutover (RET-002 RA-010 / ADR-050).
# Usage: scripts/ops/require_ci_green.sh [branch]
# Exit non-zero if watch fails — treat as hard stop unless user waives via AskQuestion.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BRANCH="${1:-$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)}"

echo "==> require_ci_green: watching required workflows on ${BRANCH}"
bash "${REPO_ROOT}/scripts/ci/watch_github_ci.sh" "${BRANCH}"
echo "==> require_ci_green: OK"

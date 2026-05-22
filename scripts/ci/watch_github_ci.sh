#!/usr/bin/env bash
# Watch latest GitHub Actions CI run for a branch (default: current).
# Usage: scripts/ci/watch_github_ci.sh [branch]
set -euo pipefail

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Latest CI runs on branch: ${BRANCH}"
gh run list --branch "$BRANCH" --workflow ci.yml --limit 3

RUN_ID="$(gh run list --branch "$BRANCH" --workflow ci.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "No CI run found for branch ${BRANCH}."
  exit 1
fi

echo "==> Watching run ${RUN_ID}"
gh run watch "$RUN_ID" --exit-status
gh run view "$RUN_ID" --json conclusion,status,headSha,url,workflowName

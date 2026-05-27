#!/usr/bin/env bash
# Watch GitHub Actions for a branch after push.
# - All branches: ci.yml (python + frontend)
# - main only: deploy-preflight.yml (build-smoke + modal-secrets)
#
# Usage: scripts/ci/watch_github_ci.sh [branch]
set -euo pipefail

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

git fetch origin "${BRANCH}" 2>/dev/null || true

if git rev-parse --verify "origin/${BRANCH}" >/dev/null 2>&1; then
  EXPECTED_SHA="$(git rev-parse "origin/${BRANCH}")"
else
  EXPECTED_SHA="$(git rev-parse "${BRANCH}")"
fi

wait_workflow_run() {
  local workflow_file="$1"
  local label="$2"

  echo ""
  echo "==> ${label} (${workflow_file}) on ${BRANCH} @ ${EXPECTED_SHA:0:7}"

  gh run list --branch "$BRANCH" --workflow "$workflow_file" --limit 5

  local run_id=""
  local attempt=0
  while (( attempt < 72 )); do
    run_id="$(
      gh run list --branch "$BRANCH" --workflow "$workflow_file" --limit 40 \
        --json databaseId,headSha \
        --jq "first(.[] | select(.headSha == \"${EXPECTED_SHA}\") | .databaseId)" 2>/dev/null || true
    )"
    if [[ -n "${run_id}" && "${run_id}" != "null" ]]; then
      break
    fi
    sleep 5
    attempt=$((attempt + 1))
  done

  if [[ -z "${run_id}" || "${run_id}" == "null" ]]; then
    echo "ERROR: No ${label} run found for commit ${EXPECTED_SHA:0:7} on ${BRANCH}." >&2
    echo "Push may not have reached GitHub yet, or workflow did not trigger." >&2
    exit 1
  fi

  echo "==> Watching run ${run_id}"
  gh run watch "${run_id}" --exit-status || true

  local conclusion status
  conclusion="$(gh run view "${run_id}" --json conclusion --jq .conclusion)"
  status="$(gh run view "${run_id}" --json status --jq .status)"

  if [[ "${conclusion}" == "cancelled" ]]; then
    echo "ERROR: ${label} run ${run_id} was cancelled (0 jobs — usually superseded by a newer push)." >&2
    echo "Do not push again until the previous watch finishes. Re-run after this commit is the branch tip:" >&2
    echo "  bash scripts/ci/watch_github_ci.sh ${BRANCH}" >&2
    exit 1
  fi

  if [[ "${conclusion}" != "success" ]]; then
    echo "ERROR: ${label} finished with conclusion=${conclusion} status=${status}" >&2
    gh run view "${run_id}" --log-failed 2>&1 | tail -40 || true
    exit 1
  fi

  gh run view "${run_id}" --json conclusion,status,headSha,url,workflowName
}

wait_workflow_run "ci.yml" "CI"

if [[ "${BRANCH}" == "main" ]]; then
  wait_workflow_run "deploy-preflight.yml" "Deploy preflight"
fi

echo ""
echo "OK: required workflows passed for ${BRANCH} @ ${EXPECTED_SHA:0:7}"

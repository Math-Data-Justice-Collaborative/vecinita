#!/usr/bin/env bash
# Cursor `afterShellExecution` hook:
# - Triggered for deploy push commands (e.g. `git push ...`, `make render-deploy-trigger`).
# - Spawns a non-blocking background collector that records:
#   1) GitHub Actions workflow runs for the current HEAD commit
#   2) Open PR details for the current branch (if one exists)
#   3) Render deploy status snapshots for configured service ids

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

INPUT="$(cat || true)"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{}'
  exit 0
fi

readarray -t PARSED < <(
  python3 - "$INPUT" <<'PY'
import json
import sys

raw = sys.argv[1]
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    print("")
    print("0")
    print("1")
    raise SystemExit(0)

command = str(payload.get("command") or "").strip()
exit_code = payload.get("exit_code")
if exit_code is None:
    exit_code = payload.get("result", {}).get("exit_code")
if exit_code is None:
    exit_code = 0

try:
    rc = int(exit_code)
except (TypeError, ValueError):
    rc = 0

print(command)
is_trigger = (
    command.startswith("git push")
    or command.startswith("make render-deploy-trigger")
    or command.startswith("make data-management")
)
print("1" if is_trigger else "0")
print(str(rc))
PY
)

COMMAND="${PARSED[0]:-}"
IS_DEPLOY_TRIGGER="${PARSED[1]:-0}"
EXIT_CODE="${PARSED[2]:-1}"

if [[ "$IS_DEPLOY_TRIGGER" != "1" ]]; then
  printf '%s\n' '{}'
  exit 0
fi

if [[ "$EXIT_CODE" != "0" ]]; then
  printf '%s\n' '{}'
  exit 0
fi

if ! command -v git >/dev/null 2>&1 || ! command -v gh >/dev/null 2>&1; then
  printf '%s\n' '{}'
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '%s\n' '{}'
  exit 0
fi

mkdir -p .cursor/hooks/logs
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE=".cursor/hooks/logs/gh-push-status-${STAMP}.log"

(
  echo "[cursor hook] gh push status collector started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[cursor hook] command: ${COMMAND}"

  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  SHA="$(git rev-parse HEAD 2>/dev/null || true)"

  if [[ -z "$BRANCH" || -z "$SHA" ]]; then
    echo "[cursor hook] unable to resolve branch/SHA; exiting."
    exit 0
  fi

  echo "[cursor hook] branch: ${BRANCH}"
  echo "[cursor hook] sha: ${SHA}"

  SERVICE_IDS=()
  for key in \
    RENDER_SERVICE_ID \
    RENDER_AGENT_SERVICE_ID \
    RENDER_GATEWAY_SERVICE_ID \
    RENDER_FRONTEND_SERVICE_ID \
    RENDER_DATA_MANAGEMENT_SERVICE_ID
  do
    value="${!key:-}"
    if [[ -n "${value}" ]]; then
      SERVICE_IDS+=("${value}")
    fi
  done

  if [[ "${#SERVICE_IDS[@]}" -gt 0 ]]; then
    # Dedupe service ids while preserving order.
    mapfile -t SERVICE_IDS < <(printf '%s\n' "${SERVICE_IDS[@]}" | awk '!seen[$0]++')
  fi

  echo
  echo "== GitHub Actions (head SHA) =="
  if ! gh run list --limit 10 --json databaseId,name,workflowName,status,conclusion,event,headBranch,headSha,url --jq ".[] | select(.headSha == \"${SHA}\") | {databaseId, workflowName, status, conclusion, event, headBranch, url}" 2>&1; then
    echo "[cursor hook] failed to fetch workflow runs."
  fi

  echo
  echo "== Pull Request (current branch) =="
  if gh pr view --json number,title,url,state,isDraft,headRefName,baseRefName --jq "{number, title, state, isDraft, headRefName, baseRefName, url}" 2>/dev/null; then
    PR_BASE="$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null || true)"
    PR_TITLE="$(gh pr view --json title --jq .title 2>/dev/null || true)"
    if [[ "$PR_BASE" == "main" ]]; then
      if [[ "${PR_TITLE,,}" != *"[render preview]"* ]]; then
        echo "[cursor hook] WARNING: PR targets main but title is missing [render preview]."
      else
        echo "[cursor hook] Render preview title token detected."
      fi
    fi
  else
    echo "[cursor hook] no open PR detected for branch ${BRANCH}."
  fi

  echo
  echo "== Render deploy status =="
  if [[ -z "${RENDER_API_KEY:-}" ]]; then
    echo "[cursor hook] RENDER_API_KEY is not set; skipping Render deploy status check."
  elif [[ ! -f "scripts/github/render_inspect.py" ]]; then
    echo "[cursor hook] scripts/github/render_inspect.py not found; skipping Render deploy status check."
  elif [[ "${#SERVICE_IDS[@]}" -eq 0 ]]; then
    echo "[cursor hook] no service ids configured. Set one or more of:"
    echo "  RENDER_SERVICE_ID, RENDER_AGENT_SERVICE_ID, RENDER_GATEWAY_SERVICE_ID,"
    echo "  RENDER_FRONTEND_SERVICE_ID, RENDER_DATA_MANAGEMENT_SERVICE_ID"
  else
    for sid in "${SERVICE_IDS[@]}"; do
      echo "-- ${sid} --"
      if ! python3 scripts/github/render_inspect.py deploys --service-id "${sid}" --limit 5 2>&1; then
        echo "[cursor hook] failed to fetch deploy status for ${sid}."
      fi
      echo
    done
  fi

  echo
  echo "[cursor hook] collector finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
) >>"$LOG_FILE" 2>&1 &

printf '%s\n' '{}'
exit 0

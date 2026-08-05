#!/usr/bin/env bash
# Upsert a sticky PR comment with unit coverage markdown (S027-D34).
# Usage: bash scripts/ci/comment_unit_coverage_pr.sh <markdown-file>
# Requires: gh, GH_TOKEN / GITHUB_TOKEN, pull_request context (or PR_NUMBER).
set -euo pipefail

MARKDOWN_FILE="${1:?usage: comment_unit_coverage_pr.sh <markdown-file>}"
MARKER="<!-- vecinita-unit-coverage -->"

if [[ ! -f "$MARKDOWN_FILE" ]]; then
  echo "error: markdown file not found: $MARKDOWN_FILE" >&2
  exit 1
fi

if [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  echo "error: GH_TOKEN or GITHUB_TOKEN required" >&2
  exit 1
fi
export GH_TOKEN="${GH_TOKEN:-$GITHUB_TOKEN}"

REPO="${GITHUB_REPOSITORY:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

PR_NUMBER="${PR_NUMBER:-}"
if [[ -z "$PR_NUMBER" && -n "${GITHUB_EVENT_PATH:-}" && -f "${GITHUB_EVENT_PATH}" ]]; then
  PR_NUMBER="$(python3 - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
pr = payload.get("pull_request") or {}
num = pr.get("number")
print(num if num is not None else "")
PY
)"
fi

if [[ -z "$PR_NUMBER" ]]; then
  echo "Skipping coverage PR comment — not a pull_request context (no PR_NUMBER)."
  exit 0
fi

BODY="$(cat "$MARKDOWN_FILE")"
if [[ "$BODY" != *"$MARKER"* ]]; then
  echo "error: markdown missing sticky marker $MARKER" >&2
  exit 1
fi

EXISTING_ID="$(
  gh api "repos/${REPO}/issues/${PR_NUMBER}/comments" --paginate \
    --jq ".[] | select(.body | contains(\"${MARKER}\")) | .id" \
    | head -n 1
)"

if [[ -n "$EXISTING_ID" ]]; then
  gh api --method PATCH "repos/${REPO}/issues/comments/${EXISTING_ID}" \
    -f body="$BODY" >/dev/null
  echo "Updated coverage PR comment id=${EXISTING_ID} on #${PR_NUMBER}"
else
  gh api --method POST "repos/${REPO}/issues/${PR_NUMBER}/comments" \
    -f body="$BODY" >/dev/null
  echo "Created coverage PR comment on #${PR_NUMBER}"
fi

#!/usr/bin/env bash
set -euo pipefail

# Rename chat frontend repository using GitHub CLI.
# Usage:
#   ./scripts/github/rename_chat_frontend_repo.sh \
#     joseph-c-mcguire Vecinitafrontend vecinita-chat-frontend

OWNER="${1:-}"
CURRENT_NAME="${2:-}"
NEW_NAME="${3:-}"

if [[ -z "$OWNER" || -z "$CURRENT_NAME" || -z "$NEW_NAME" ]]; then
  echo "Usage: $0 <owner> <current-name> <new-name>"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required."
  exit 1
fi

REPO_PATH="$OWNER/$CURRENT_NAME"

echo "About to rename $REPO_PATH -> $NEW_NAME"
echo "This operation changes clone URLs and integration references."
read -r -p "Continue? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted"
  exit 1
fi

gh api \
  --method PATCH \
  "repos/$REPO_PATH" \
  -f name="$NEW_NAME"

echo "Repository renamed successfully."
echo "Next: update .github/workflows/multi-repo-release-orchestrator.yml target_repo mapping."

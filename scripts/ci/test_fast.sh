#!/usr/bin/env bash
# Run unit tests only for components touched by local changes (staged, unstaged, untracked).
# Used by `make test-fast`, the Cursor stop hook, and Husky pre-push.
# Full CI parity: `make ci-push` before opening a PR.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

collect_changed() {
	{
		git diff --name-only HEAD 2>/dev/null || true
		git diff --name-only --cached 2>/dev/null || true
		git ls-files --other --exclude-standard 2>/dev/null || true
	} | awk 'NF && !seen[$0]++'
}

mapfile -t CHANGED < <(collect_changed)
if ((${#CHANGED[@]} == 0)); then
	echo "test-fast: no local changes; skipping"
	exit 0
fi

RUN_PY=false
declare -A FE_WS=()

for f in "${CHANGED[@]}"; do
	case "$f" in
	apps/chat-rag-frontend/*) FE_WS[vecinita-chat-rag-frontend]=1 ;;
	apps/data-management-frontend/*) FE_WS[vecinita-data-management-frontend]=1 ;;
	packages/frontend-i18n/*) FE_WS[vecinita-frontend-i18n]=1 ;;
	packages/frontend-ui/*) FE_WS[vecinita-frontend-ui]=1 ;;
	packages/* | apps/* | tests/*) RUN_PY=true ;;
	esac
done

if [[ "$RUN_PY" == true ]]; then
	echo "==> test-fast: pytest tests/unit"
	uv run pytest tests/unit -q --tb=line
fi

for ws in "${!FE_WS[@]}"; do
	echo "==> test-fast: npm test -w ${ws}"
	bash scripts/npm_with_lock.sh npm test -w "${ws}"
done

if [[ "$RUN_PY" != true && ${#FE_WS[@]} -eq 0 ]]; then
	echo "test-fast: no testable source changes; skipping"
fi

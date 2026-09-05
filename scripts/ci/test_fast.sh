#!/usr/bin/env bash
# Run unit tests only for components touched by local changes (staged, unstaged, untracked).
# Used by `make test-fast`, the Cursor stop hook, and Husky pre-push.
# Full CI parity: `make ci-push` before opening a PR.
#
# Portable for macOS /bin/bash 3.2 (S031): avoid bash-4-only builtins.
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

# Newline-delimited unique membership (bash 3.2 — no associative arrays).
list_has() {
	# $1 = needle, $2 = newline-delimited haystack
	local needle="$1"
	local haystack="${2-}"
	[[ -n "$haystack" ]] || return 1
	printf '%s\n' "$haystack" | grep -Fxq -- "$needle"
}

list_add() {
	# stdout = haystack with needle appended if missing
	local needle="$1"
	local haystack="${2-}"
	if list_has "$needle" "$haystack"; then
		printf '%s' "$haystack"
		return 0
	fi
	if [[ -n "$haystack" ]]; then
		printf '%s\n%s' "$haystack" "$needle"
	else
		printf '%s' "$needle"
	fi
}

CHANGED=""
while IFS= read -r line || [[ -n "$line" ]]; do
	[[ -z "$line" ]] && continue
	if [[ -n "$CHANGED" ]]; then
		CHANGED="${CHANGED}"$'\n'"${line}"
	else
		CHANGED="${line}"
	fi
done < <(collect_changed)

if [[ -z "$CHANGED" ]]; then
	echo "test-fast: no local changes; skipping"
	exit 0
fi

PY_PATHS=""
FE_WS=""
RUN_ALL_UNIT=false

while IFS= read -r f || [[ -n "$f" ]]; do
	[[ -z "$f" ]] && continue
	case "$f" in
	apps/chat-rag-frontend/*) FE_WS="$(list_add "vecinita-chat-rag-frontend" "$FE_WS")" ;;
	apps/data-management-frontend/*) FE_WS="$(list_add "vecinita-data-management-frontend" "$FE_WS")" ;;
	packages/frontend-i18n/*) FE_WS="$(list_add "vecinita-frontend-i18n" "$FE_WS")" ;;
	packages/frontend-ui/*) FE_WS="$(list_add "vecinita-frontend-ui" "$FE_WS")" ;;
	apps/chat-rag-backend/*) PY_PATHS="$(list_add "tests/unit/chat_rag" "$PY_PATHS")" ;;
	apps/data-management-backend/*) PY_PATHS="$(list_add "tests/unit/data_management" "$PY_PATHS")" ;;
	apps/internal-write-api/*) PY_PATHS="$(list_add "tests/unit/internal_write_api" "$PY_PATHS")" ;;
	apps/database/*) PY_PATHS="$(list_add "tests/unit/database" "$PY_PATHS")" ;;
	packages/ingest/*) PY_PATHS="$(list_add "tests/unit/ingest" "$PY_PATHS")" ;;
	packages/rag/*) PY_PATHS="$(list_add "tests/unit/rag" "$PY_PATHS")" ;;
	packages/shared-schemas/*) PY_PATHS="$(list_add "tests/unit/shared_schemas" "$PY_PATHS")" ;;
	packages/eval/*) PY_PATHS="$(list_add "tests/unit/eval" "$PY_PATHS")" ;;
	packages/tagging/*) PY_PATHS="$(list_add "tests/unit/tagging" "$PY_PATHS")" ;;
	packages/llm-client/*)
		PY_PATHS="$(list_add "tests/unit/test_llm_client.py" "$PY_PATHS")"
		PY_PATHS="$(list_add "tests/unit/test_llm_tag_client.py" "$PY_PATHS")"
		PY_PATHS="$(list_add "tests/unit/test_llm_app_snapshot_prep.py" "$PY_PATHS")"
		PY_PATHS="$(list_add "tests/unit/test_llm_app_enforce_eager_ab.py" "$PY_PATHS")"
		;;
	packages/embedding-client/*) PY_PATHS="$(list_add "tests/unit/test_embedding_client.py" "$PY_PATHS")" ;;
	scripts/*) PY_PATHS="$(list_add "tests/unit/scripts" "$PY_PATHS")" ;;
	infra/* | .github/workflows/*)
		PY_PATHS="$(list_add "tests/unit/test_shell_deploy_guard.py" "$PY_PATHS")"
		PY_PATHS="$(list_add "tests/unit/scripts" "$PY_PATHS")"
		;;
	tests/unit/*)
		if [[ -f "$f" ]]; then
			PY_PATHS="$(list_add "$f" "$PY_PATHS")"
		else
			PY_PATHS="$(list_add "$(dirname "$f")" "$PY_PATHS")"
		fi
		;;
	pyproject.toml | uv.lock | Makefile | package.json | package-lock.json)
		RUN_ALL_UNIT=true
		;;
	packages/* | apps/* | tests/*)
		RUN_ALL_UNIT=true
		;;
	esac
done <<<"$CHANGED"

if [[ "$RUN_ALL_UNIT" == true ]]; then
	echo "==> test-fast: pytest tests/unit (broad change)"
	uv run pytest tests/unit -q --tb=line
elif [[ -n "$PY_PATHS" ]]; then
	# shellcheck disable=SC2086 # intentional word-split of sorted paths
	PY_ARGS="$(printf '%s\n' "$PY_PATHS" | sort -u | tr '\n' ' ')"
	echo "==> test-fast: pytest ${PY_ARGS}"
	# shellcheck disable=SC2086
	uv run pytest ${PY_ARGS} -q --tb=line
fi

if [[ -n "$FE_WS" ]]; then
	while IFS= read -r ws || [[ -n "$ws" ]]; do
		[[ -z "$ws" ]] && continue
		echo "==> test-fast: npm test -w ${ws}"
		bash scripts/npm_with_lock.sh npm test -w "${ws}"
	done <<<"$FE_WS"
fi

if [[ "$RUN_ALL_UNIT" != true && -z "$PY_PATHS" && -z "$FE_WS" ]]; then
	echo "test-fast: no testable source changes; skipping"
fi

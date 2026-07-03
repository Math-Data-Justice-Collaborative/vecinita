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

add_py_path() {
	PY_PATHS["$1"]=1
}

mapfile -t CHANGED < <(collect_changed)
if ((${#CHANGED[@]} == 0)); then
	echo "test-fast: no local changes; skipping"
	exit 0
fi

declare -A PY_PATHS=()
declare -A FE_WS=()
RUN_ALL_UNIT=false

for f in "${CHANGED[@]}"; do
	case "$f" in
	apps/chat-rag-frontend/*) FE_WS[vecinita-chat-rag-frontend]=1 ;;
	apps/data-management-frontend/*) FE_WS[vecinita-data-management-frontend]=1 ;;
	packages/frontend-i18n/*) FE_WS[vecinita-frontend-i18n]=1 ;;
	packages/frontend-ui/*) FE_WS[vecinita-frontend-ui]=1 ;;
	apps/chat-rag-backend/*) add_py_path tests/unit/chat_rag ;;
	apps/data-management-backend/*) add_py_path tests/unit/data_management ;;
	apps/internal-write-api/*) add_py_path tests/unit/internal_write_api ;;
	apps/database/*) add_py_path tests/unit/database ;;
	packages/ingest/*) add_py_path tests/unit/ingest ;;
	packages/rag/*) add_py_path tests/unit/rag ;;
	packages/shared-schemas/*) add_py_path tests/unit/shared_schemas ;;
	packages/eval/*) add_py_path tests/unit/eval ;;
	packages/tagging/*) add_py_path tests/unit/tagging ;;
	packages/llm-client/*)
		add_py_path tests/unit/test_llm_client.py
		add_py_path tests/unit/test_llm_tag_client.py
		add_py_path tests/unit/test_llm_app_snapshot_prep.py
		add_py_path tests/unit/test_llm_app_enforce_eager_ab.py
		;;
	packages/embedding-client/*) add_py_path tests/unit/test_embedding_client.py ;;
	scripts/*) add_py_path tests/unit/scripts ;;
	infra/* | .github/workflows/*)
		add_py_path tests/unit/test_shell_deploy_guard.py
		add_py_path tests/unit/scripts
		;;
	tests/unit/*)
		if [[ -f "$f" ]]; then
			add_py_path "$f"
		else
			add_py_path "$(dirname "$f")"
		fi
		;;
	pyproject.toml | uv.lock | Makefile | package.json | package-lock.json)
		RUN_ALL_UNIT=true
		;;
	packages/* | apps/* | tests/*)
		RUN_ALL_UNIT=true
		;;
	esac
done

if [[ "$RUN_ALL_UNIT" == true ]]; then
	echo "==> test-fast: pytest tests/unit (broad change)"
	uv run pytest tests/unit -q --tb=line
elif ((${#PY_PATHS[@]} > 0)); then
	mapfile -t PY_ARGS < <(printf '%s\n' "${!PY_PATHS[@]}" | sort -u)
	echo "==> test-fast: pytest ${PY_ARGS[*]}"
	uv run pytest "${PY_ARGS[@]}" -q --tb=line
fi

for ws in "${!FE_WS[@]}"; do
	echo "==> test-fast: npm test -w ${ws}"
	bash scripts/npm_with_lock.sh npm test -w "${ws}"
done

if [[ "$RUN_ALL_UNIT" != true && ${#PY_PATHS[@]} -eq 0 && ${#FE_WS[@]} -eq 0 ]]; then
	echo "test-fast: no testable source changes; skipping"
fi

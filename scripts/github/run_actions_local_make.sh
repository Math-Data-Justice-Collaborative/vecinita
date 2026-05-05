#!/usr/bin/env bash
# Local parity for .github/workflows/*.yml without nektos/act (no Docker required).
# Skips workflows that only run on GitHub (cross-repo, post-deploy, secrets/URLs).
#
# Optional env:
#   RUN_PLAYWRIGHT=1     Run frontend Playwright e2e locally (optional; not part of GitHub test.yml).
#   RUN_PGVECTOR=1       Run DB integration tests against a local pgvector (advanced).
#   RUN_MICROSERVICES=1  Force microservices stack test even if Docker check fails (not recommended).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

skip() {
	echo ""
	echo "[skip] $1"
	echo "       $2"
}

section() {
	echo ""
	echo "================================================================================"
	echo " $1"
	echo "================================================================================"
}

have_docker() {
	command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

section "reusable-dispatch-repo-workflow.yml"
skip "reusable-dispatch-repo-workflow.yml" "workflow_call only — runs when invoked from another workflow on GitHub."

section "render-post-deploy.yml"
skip "render-post-deploy.yml" "workflow_run after Render Deploy — not replayable locally."

section "multi-repo-release-orchestrator.yml"
skip "multi-repo-release-orchestrator.yml" "Dispatches other repositories — GitHub-only."

section "modal-deploy.yml"
skip "modal-deploy.yml" "Modal deploy — requires MODAL_TOKEN and Modal CLI outside this script."

section "quality-gate.yml"
echo "quality-gate.yml checks are included in \`make ci\` (via quality-full → quality)."

section "env-sync-contract.yml"
(
	cd apis/gateway
	SKIP_AGENT_MAIN_IMPORT=true uv run python -m pytest tests/contracts/test_env_sync_contract.py tests/contracts/test_env_sync_github_actions_bundle.py -v --tb=short -m contract
)

section "render-deploy.yml (validate env + gateway profile)"
python3 scripts/github/validate_render_env.py .env.prod.render
python3 scripts/github/validate_render_env.py .env.staging.render
python3 scripts/github/validate_render_env_parity.py .env.prod.render .env.staging.render
python3 scripts/github/validate_gateway_dependency_profile.py

section "test.yml — secret-scan (gitleaks)"
if command -v gitleaks >/dev/null 2>&1; then
	set +e
	gitleaks dir . --redact --config .gitleaks.toml
	gl=$?
	set -e
	if [[ "$gl" -ne 0 ]]; then
		echo "warning: gitleaks reported findings (CI treats this as warning). Review .gitleaks.toml if needed."
	fi
else
	skip "gitleaks" "not installed — install from https://github.com/gitleaks/gitleaks for secret-scan parity."
fi

section "test.yml — core quality + tests (ci)"
make ci

section "test.yml — OpenAPI schema / Schemathesis"
make test-schemathesis

section "render / offline contracts (render-workflow-ci, connectivity)"
make render-workflow-ci render-connectivity-tests

section "backend-coverage.yml"
(
	cd apis/gateway
	: >.env
	{
		echo "DATABASE_URL=postgresql://test"
		echo "OLLAMA_BASE_URL=http://localhost:11434"
		echo "OLLAMA_MODEL=llama3.1:8b"
		echo "USE_LOCAL_EMBEDDINGS=true"
		echo "EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2"
		echo "EMBEDDING_SERVICE_AUTH_TOKEN=test-embed-token"
		echo "EMBEDDING_STRICT_STARTUP=false"
		echo "REINDEX_TRIGGER_TOKEN=test-reindex-token"
		echo "REINDEX_SERVICE_URL=https://example.modal.run"
	} >>.env
	export PYTHONPATH="${ROOT}/apis/gateway:${ROOT}/modal-apps/embedding-modal/src"
	export SKIP_AGENT_MAIN_IMPORT=true
	export EMBEDDING_STRICT_STARTUP=false
	uv run pytest tests/ -m "not integration and not e2e and not llm" -v --tb=short \
		--cov=vecinita.app \
		--cov=src.services.embedding.models \
		--cov=src.utils.tags \
		--cov-config=.coveragerc.unit --cov-report=term \
		--cov-fail-under=98
)

section "frontend-coverage.yml"
(
	cd frontends/chat
	npm ci
	npm run test:coverage:unit
)

section "docs-gh-pages.yml (build only)"
make docs-install docs-build

section "microservices-contracts.yml"
if [[ "${RUN_MICROSERVICES:-}" == "1" ]] || have_docker; then
	make test-microservices
else
	skip "microservices-contracts (docker compose stack)" "Docker not available. Start Docker and re-run, or RUN_MICROSERVICES=1 make actions-local (will likely fail without Docker)."
fi

section "Playwright e2e (optional; local only — not in CI)"
if [[ "${RUN_PLAYWRIGHT:-}" == "1" ]]; then
	make test-frontend-e2e
else
	skip "Playwright e2e" "set RUN_PLAYWRIGHT=1 to run Playwright (requires stack; slow)."
fi

section "test.yml — pgvector integration (optional)"
skip "test.yml backend-integration-pgvector" "needs Postgres+pgvector + migrations (see test.yml job backend-integration-pgvector). Set RUN_PGVECTOR=1 in the future for scripted local runs, or use GitHub Actions."

section "Done"
echo "Local workflow parity run finished (see skips above for GitHub-only or optional sections)."

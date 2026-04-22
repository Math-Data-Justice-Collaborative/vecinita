.PHONY: help \
	dev dev-tmux dev-attach dev-stop dev-clear-ports \
	dev-chat dev-chat-backend dev-chat-gateway dev-chat-frontend \
	dev-data-management dev-data-management-frontend dev-data-management-api data-management-api-key data-management \
	dev-backend dev-gateway dev-frontend \
	branch-status branch-save branch-restore branch-switch branch-pull branch-sync-main actions-status actions-failures actions-logs \
	actions-local actions-local-act actions-local-list \
	lint lint-backend lint-frontend lint-imported lint-fix lint-fix-backend lint-fix-frontend lint-fix-data-management-frontend \
	typecheck typecheck-backend typecheck-frontend typecheck-imported \
	format format-backend format-frontend format-check format-check-backend format-check-frontend \
	audit audit-backend audit-frontend audit-imported audit-data-management-frontend audit-fix audit-fix-frontend audit-fix-data-management-frontend \
	quality quality-fix quality-full ci quality-imported \
	test-unit test-integration test-e2e \
	test-backend-unit test-frontend-unit test-frontend-e2e \
	test-imported test-data-management-frontend test-embedding-modal test-model-modal test-scraper check-data-management-api-layout \
	lint-data-management-frontend lint-scraper lint-embedding-modal lint-model-modal \
	typecheck-scraper \
	test-integration-gateway-fast test-integration-gateway-full test-integration-gateway \
	test-all-integration test-cross-integration test-cross-e2e \
	test-schemathesis test-schemathesis-gateway test-schemathesis-gateway-stateful test-schemathesis-agent test-schemathesis-data-management test-schemathesis-cli test-schemathesis-cli-agent \
	test-fr005-schemathesis-baseline dm-openapi-diff pact-verify-providers \
	scraper-run scraper-run-verbose scraper-run-clean scraper-validate-postgres scraper-pull \
	microservices-up microservices-down microservices-logs test-microservices-contracts test-microservices \
	render-env-validate render-tests-strict render-tests-render-suite render-workflow-ci \
	render-local-up render-local-down render-local-logs render-local-check render-local-check-live render-local-validate \
	env-sync-contract render-connectivity-tests render-all-offline-contract-tests \
	render-deploy-trigger render-deploy-wait \
	render-services render-deploy-status render-deploy-show render-service-env render-logs \
	docs-install docs-serve docs-build docs-deploy-check

help:
	@echo "Vecinita root Makefile"
	@echo ""
	@echo "Development targets"
	@echo "  make dev                                 Start full local dev stack with cascading logs"
	@echo "  make dev-chat                            Start chat application (frontend + gateway + agent)"
	@echo "  make dev-chat-frontend                   Start chat frontend dev server only"
	@echo "  make dev-chat-backend                    Start chat backend services (gateway + agent)"
	@echo "  make dev-data-management                 Start data management system (frontend + API)"
	@echo "  make dev-data-management-frontend        Start data management frontend only"
	@echo "  make dev-data-management-api             Start data management API only"
	@echo "  make data-management                     Trigger data management frontend Render deploy"
	@echo "  make data-management-api-key             Print configured dashboard API key or guidance"
	@echo "  make dev-tmux                            Start the legacy tmux split-pane dev session"
	@echo "  make dev-attach                          Attach to the existing tmux dev session"
	@echo "  make dev-stop                            Stop the dev session and local containers"
	@echo "  make dev-clear-ports                     Kill processes bound to local dev ports"
	@echo "  make dev-backend                         Start the backend agent in reload mode"
	@echo "  make dev-gateway                         Start the API gateway in reload mode"
	@echo "  make dev-frontend                        Start the frontend dev server"
	@echo ""
	@echo "Branch workflow targets"
	@echo "  make branch-status                       Show component branch and dirty state"
	@echo "  make branch-save                         Save current branch snapshot"
	@echo "  make branch-switch BRANCH=<name>         Switch components to branch, fallback to main"
	@echo "  make branch-pull [BRANCH=<name>]         Pull latest from origin for component branches"
	@echo "  make branch-restore                      Restore last saved branch snapshot"
	@echo "  make branch-sync-main                    Switch all components to main"
	@echo ""
	@echo "GitHub Actions (GitHub CLI)"
	@echo "  make actions-status                      List recent workflow runs for this repo (requires gh)"
	@echo "    REPO=owner/name WORKFLOW=ci.yml BRANCH=main STATUS=failure LIMIT=10  Optional filters"
	@echo "  make actions-failures                    List recent failed runs (same optional filters except STATUS)"
	@echo "  make actions-logs RUN=<run-id>           Stream logs for a run (failed steps by default; LOG=full for all)"
	@echo "    REPO=... JOB=<job-id>                  Optional repo override or single-job logs"
	@echo "  make actions-local [WORKFLOW=test.yml]   Local parity vs .github/workflows (no act required; optional USE_ACT=1)"
	@echo "    RUN_PLAYWRIGHT=1 RUN_MICROSERVICES=1      Optional heavy steps (see scripts/github/run_actions_local_make.sh)"
	@echo "  make actions-local-act [WORKFLOW=...]    Same as actions-local but requires nektos/act + Docker"
	@echo "    ARGS='-n' ACT_EVENT=push ACT_SKIP=...  Optional act flags when USE_ACT=1"
	@echo "  make actions-local-list WORKFLOW=test.yml  List jobs/events for one workflow (requires act)"
	@echo ""
	@echo "Quality targets"
	@echo "  make lint                                Lint core and imported codebases"
	@echo "  make lint-imported                       Lint imported service/frontend sub-repos"
	@echo "  make lint-backend                        Run Ruff checks"
	@echo "  make lint-frontend                       Run ESLint checks"
	@echo "  make lint-fix                            Auto-fix supported lint issues"
	@echo "  make typecheck                           Type-check core and imported codebases"
	@echo "  make typecheck-imported                  Run imported sub-repo type checks"
	@echo "  make typecheck-backend                   Run mypy on backend source"
	@echo "  make typecheck-frontend                  Run TypeScript checks"
	@echo "  make format                              Format backend and frontend"
	@echo "  make format-backend                      Format backend with Black (src, tests, scripts)"
	@echo "  make format-frontend                     Format frontend with Prettier"
	@echo "  make format-check                        Check formatting without writing"
	@echo "  make audit                               Run dependency audits for backend and frontend"
	@echo "  make audit-imported                      Run dependency audits for imported frontend repos"
	@echo "  make quality-imported                    Run imported sub-repo quality checks"
	@echo "  make quality                             Run repo-wide lint, format, typecheck, and audit checks"
	@echo "  make quality-fix                         Apply safe auto-fixes, then rerun quality checks"
	@echo "  make quality-full                        Sequential: quality → unit → imported → gateway matrix → service integration contracts (stops on first failure)"
	@echo "  make ci                                  Same as quality-full (local CI gate; .cursor stop hook runs this)"
	@echo ""
	@echo "Testing targets"
	@echo "  make test-unit                           Run backend and frontend unit tests"
	@echo "  make test-backend-unit                   Run backend unit tests"
	@echo "  make test-frontend-unit                  Run frontend unit tests"
	@echo "  make test-imported                       Run imported sub-repo test suites"
	@echo "  make test-integration                    Run backend and cross-stack integration tests"
	@echo "  make test-integration-gateway-fast       Run gateway matrix contract checks"
	@echo "  make test-integration-service-contracts   Run SERVICE_INTEGRATION_POINTS contract tests (matches CI backend-integration slice)"
	@echo "  make test-integration-gateway-full       Run gateway-focused integration suites"
	@echo "  make test-integration-gateway            Alias of full gateway integration"
	@echo "  make test-all-integration                Run all backend integration tests"
	@echo "  make test-cross-integration              Run tests/ integration suite"
	@echo "  make test-microservices-contracts        Run model/embedding/scraper contract tests"
	@echo "  make test-microservices                  Start stack, run contracts, stop stack"
	@echo "  make test-e2e                            Run frontend and cross-stack e2e tests"
	@echo "  make test-cross-e2e                      Run tests/ e2e suite"
	@echo "  make test-frontend-e2e                   Run frontend Playwright tests"
	@echo ""
	@echo "Schemathesis (OpenAPI contract)"
	@echo "  make test-schemathesis                   Run gateway + agent + data-management Schemathesis pytest suites (TraceCov per suite)"
	@echo "  make test-schemathesis-gateway           Gateway ASGI schema tests (mocked upstreams)"
	@echo "  make test-schemathesis-gateway-stateful  Gateway job stateful Schemathesis (pytest; mocked)"
	@echo "  make test-schemathesis-agent             Agent ASGI schema tests (mocked LLM/embeddings)"
	@echo "  make test-schemathesis-data-management   Live lx27 data-management API; TraceCov fail-under 100 (needs SCRAPER_API_KEYS)"
	@echo "  make test-schemathesis-cli               Live Schemathesis CLI (loads .env): gateway + data-management; optional AGENT_SCHEMA_URL"
	@echo "  make test-schemathesis-cli-agent         Live pytest Schemathesis against deployed agent (RENDER_AGENT_URL from .env)"
	@echo "  make test-fr005-schemathesis-baseline    Gateway + agent Schemathesis pytest (FR-005 / T032)"
	@echo "  make dm-openapi-diff                     Diff DM OpenAPI vs committed snapshot (FR-004 / SC-002)"
	@echo "  make pact-verify-providers               Replay Pact consumers against live providers (FR-007/008; needs env + pacts)"
	@echo ""
	@echo "Scraper and ingestion targets"
	@echo "  make scraper-run                         Run scraper in additive streaming mode"
	@echo "  make scraper-run-verbose                 Run scraper with verbose logs and DB validation"
	@echo "  make scraper-run-clean                   Run destructive clean + scraper + DB validation"
	@echo "  make scraper-pull                        Fetch/rebase services/scraper (fixes fast-forward pull failures)"
	@echo "  make scraper-validate-postgres           Run Postgres validation queries only (no scraping)"
	@echo ""
	@echo "Render workflow shortcuts"
	@echo "  make render-env-validate [ENV_FILE=...]  Validate shared Render env contract"
	@echo "  make render-tests-render-suite           Run Render-focused direct-endpoint backend tests"
	@echo "  make render-tests-strict                 Run strict-mode fail-fast e2e tests"
	@echo "  make render-tests-render-suite           Run full Render-focused backend test suite"
	@echo "  make render-workflow-ci                  Validate env + run render-focused tests"
	@echo "  make render-local-up                     Start local Render-like compose overlay"
	@echo "  make render-local-down                   Stop local Render-like compose overlay"
	@echo "  make render-local-logs                   Tail local Render-like compose logs"
	@echo "  make render-local-validate [ENV_FILE=...] Validate env contract + compose syntax"
	@echo "  make render-local-check [ENV_FILE=...]   Smart check: preflight always, live checks if stack is up"
	@echo "  make render-local-check-live [ENV_FILE=...] Force live local Render smoke/runbook checks"
	@echo ""
	@echo "Env key standardization + contract tests"
	@echo "  make env-sync-contract                   Cross-platform env key sync contract tests (no secrets)"
	@echo "  make render-connectivity-tests           Render connectivity config tests (offline)"
	@echo "  make render-all-offline-contract-tests   Run all offline contract tests"
	@echo "Deploy management (requires RENDER_*_DEPLOY_HOOK_URL / RENDER_API_KEY)"
	@echo "  make render-deploy-trigger               Fire Render deploy hooks for all services"
	@echo "  make render-deploy-wait SERVICE_ID=...   Wait for a Render deploy to reach live status"
	@echo "Render API inspect (requires RENDER_API_KEY; see https://dashboard.render.com/api-keys)"
	@echo "  make render-services [LIMIT=50]        List service ids + names for this API key"
	@echo "  make render-deploy-status [SERVICE_ID=]  Recent deploys (SERVICE_ID or RENDER_*_SERVICE_ID env)"
	@echo "  make render-deploy-show DEPLOY=dep-... [SERVICE_ID=]  Full JSON for one deploy"
	@echo "  make render-service-env [SERVICE_ID=]    Env keys + binding kinds (secret values not returned by API)"
	@echo "  make render-logs [LOG_TYPE=build] ...  Recent logs (omit LOG_TYPE for all types Render returns)"
	@echo "    After render login: render logs -r srv-... -o text --type build"
	@echo ""
	@echo "Microservices stack targets"
	@echo "  make microservices-up                    Start microservices compose stack"
	@echo "  make microservices-down                  Stop microservices compose stack"
	@echo "  make microservices-logs                  Tail microservices compose logs"
	@echo ""
	@echo "Documentation targets"
	@echo "  make docs-install                        Install Docusaurus dependencies"
	@echo "  make docs-serve                          Start docs site locally"
	@echo "  make docs-build                          Build docs site"
	@echo "  make docs-deploy-check                   Validate docs build for Pages"

dev:
	./run/dev-session.sh start

dev-tmux:
	./run/dev-session.sh start-tmux

dev-attach:
	./run/dev-session.sh attach

dev-stop:
	./run/dev-session.sh stop

dev-clear-ports:
	@for port in 5173 5174 8000 8001 8004 8005; do \
		pids="$$( (command -v lsof >/dev/null 2>&1 && lsof -ti tcp:$$port 2>/dev/null) || (command -v fuser >/dev/null 2>&1 && fuser -n tcp $$port 2>/dev/null) || true )"; \
		if [ -n "$$pids" ]; then \
			echo "Clearing port $$port (PID(s): $$pids)"; \
			kill -9 $$pids 2>/dev/null || true; \
		else \
			echo "Port $$port already free"; \
		fi; \
	done

dev-backend:
	cd backend && \
		uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc'

dev-gateway:
	cd backend && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='http://localhost:8001' \
		DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' \
		DEMO_MODE='false' \
		uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc'

dev-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

# ============================================================================
# Chat Application (Frontend + Gateway + Agent)
# ============================================================================

dev-chat: dev-chat-backend dev-chat-frontend
	@echo "Chat application started: Frontend on port 5173, Gateway on port 8004, Agent on port 8000"

dev-chat-backend: dev-chat-agent dev-chat-gateway

dev-chat-agent:
	@echo "Starting Chat Agent (port 8000)..."
	@cd backend && \
		uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc' &

dev-chat-gateway:
	@echo "Starting Chat Gateway (port 8004, PostgreSQL-backed)..."
	@cd backend && source ../.env && \
		AGENT_SERVICE_URL='http://localhost:8000' \
		EMBEDDING_SERVICE_URL='http://localhost:8001' \
		DEV_ADMIN_ENABLED='true' \
		DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' \
		uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc' &

dev-chat-frontend:
	@echo "Starting Chat Frontend (port 5173)..."
	@cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

# ============================================================================
# Data Management System (Frontend + API)
# ============================================================================

dev-data-management: dev-data-management-api dev-data-management-frontend
	@echo "Data Management system started: Frontend on port 5174, API on port 8005"

dev-data-management-frontend:
	@echo "Starting Data Management Frontend (port 5174)..."
	@cd apps/data-management-frontend && npm run dev -- --host 0.0.0.0 --port 5174

dev-data-management-api:
	@echo "Starting Data Management API (port 8005, PostgreSQL-backed)..."
	@test -d services/data-management-api/apps/backend || \
		(echo "❌ data-management-api submodule not initialized." && \
		 echo "   Run: git submodule update --init services/data-management-api" && exit 1)
	@echo "⚠️  Start data-management API directly from services/data-management-api using its native entrypoint." 

data-management-api-key:
	@set -e; \
	if [ -n "$$DATA_MANAGEMENT_API_KEY" ]; then \
		echo "$$DATA_MANAGEMENT_API_KEY"; \
	elif [ -n "$$DEV_ADMIN_BEARER_TOKEN" ]; then \
		echo "$$DEV_ADMIN_BEARER_TOKEN"; \
	elif [ -f .env ] && grep -q '^DATA_MANAGEMENT_API_KEY=' .env; then \
		grep '^DATA_MANAGEMENT_API_KEY=' .env | tail -n 1 | cut -d= -f2-; \
	elif [ -f .env ] && grep -q '^DEV_ADMIN_BEARER_TOKEN=' .env; then \
		grep '^DEV_ADMIN_BEARER_TOKEN=' .env | tail -n 1 | cut -d= -f2-; \
	elif [ -f services/data-management-api/.env ] && grep -q '^DATA_MANAGEMENT_API_KEY=' services/data-management-api/.env; then \
		grep '^DATA_MANAGEMENT_API_KEY=' services/data-management-api/.env | tail -n 1 | cut -d= -f2-; \
	elif [ -f services/data-management-api/.env ] && grep -q '^DEV_ADMIN_BEARER_TOKEN=' services/data-management-api/.env; then \
		grep '^DEV_ADMIN_BEARER_TOKEN=' services/data-management-api/.env | tail -n 1 | cut -d= -f2-; \
	else \
		echo "No DATA_MANAGEMENT_API_KEY is configured."; \
		echo "No DATA_MANAGEMENT_API_KEY or DEV_ADMIN_BEARER_TOKEN is configured."; \
		echo "This repo does not mint dashboard API keys automatically."; \
		echo "Ask the data-management backend operator for a provisioned key, then export DATA_MANAGEMENT_API_KEY=<token> or add it to .env."; \
		exit 1; \
	fi

data-management:
	@echo "Triggering data-management frontend deploy..."
	@set -e; \
		hook_url="$${RENDER_DATA_MANAGEMENT_FRONTEND_DEPLOY_HOOK_URL:-$${DATA_MANAGEMENT_FRONTEND_DEPLOY_HOOK_URL:-$${RENDER_DEPLOY_HOOK_URL:-}}}"; \
		if [ -z "$$hook_url" ]; then \
			echo "No deploy hook configured for data-management frontend."; \
			echo "Set one of: RENDER_DATA_MANAGEMENT_FRONTEND_DEPLOY_HOOK_URL, DATA_MANAGEMENT_FRONTEND_DEPLOY_HOOK_URL, or RENDER_DEPLOY_HOOK_URL"; \
			exit 1; \
		fi; \
		curl -fsSL -X POST "$$hook_url"; \
		echo "Data-management frontend deploy triggered."
# Individual service targets (legacy)
# ============================================================================

branch-status:
	./run/branch-orchestrator.sh status
	./run/branch-orchestrator.sh save

branch-save:
	./run/branch-orchestrator.sh save

branch-restore:
	./run/branch-orchestrator.sh restore

branch-switch:
	@test -n "$(BRANCH)" || (echo "Usage: make branch-switch BRANCH=<name>" && exit 1)
	./run/branch-orchestrator.sh switch "$(BRANCH)"

branch-pull:
	@if [ -n "$(BRANCH)" ]; then \
		./run/branch-orchestrator.sh pull "$(BRANCH)"; \
	else \
		./run/branch-orchestrator.sh pull; \
	fi

branch-sync-main:
	./run/branch-orchestrator.sh sync-main

actions-status:
	@command -v gh >/dev/null 2>&1 || (echo "GitHub CLI (gh) is not installed. See https://cli.github.com/" && exit 1)
	gh run list $(if $(REPO),-R $(REPO),) $(if $(WORKFLOW),-w $(WORKFLOW),) $(if $(BRANCH),-b $(BRANCH),) $(if $(STATUS),-s $(STATUS),) --limit $(or $(LIMIT),20)

actions-failures:
	@command -v gh >/dev/null 2>&1 || (echo "GitHub CLI (gh) is not installed. See https://cli.github.com/" && exit 1)
	gh run list $(if $(REPO),-R $(REPO),) $(if $(WORKFLOW),-w $(WORKFLOW),) $(if $(BRANCH),-b $(BRANCH),) -s failure --limit $(or $(LIMIT),20)

actions-logs:
	@command -v gh >/dev/null 2>&1 || (echo "GitHub CLI (gh) is not installed. See https://cli.github.com/" && exit 1)
	@test -n "$(RUN)" || (echo "Usage: make actions-logs RUN=<run-id>  (numeric id from make actions-failures or make actions-status)" && exit 1)
	gh run view $(RUN) $(if $(REPO),-R $(REPO),) $(if $(JOB),--job $(JOB),) $(if $(filter full,$(LOG)),--log,--log-failed)

# Local parity with GitHub workflows: default runs scripts/github/run_actions_local_make.sh (no act).
# USE_ACT=1 uses nektos/act when installed. See scripts/github/run_actions_local_make.sh for env vars.
actions-local:
	@WORKFLOW="$(WORKFLOW)" ACT_EVENT="$(ACT_EVENT)" ACT_SKIP="$(ACT_SKIP)" ACT_RUNNER_IMAGE="$(ACT_RUNNER_IMAGE)" \
		USE_ACT="$(USE_ACT)" ./scripts/github/actions_local.sh $(ARGS)

# Requires Docker + act: https://github.com/nektos/act
actions-local-act:
	@command -v act >/dev/null 2>&1 || (echo "act is not installed. See https://github.com/nektos/act#installation" && exit 1)
	@WORKFLOW="$(WORKFLOW)" ACT_EVENT="$(ACT_EVENT)" ACT_SKIP="$(ACT_SKIP)" ACT_RUNNER_IMAGE="$(ACT_RUNNER_IMAGE)" \
		./scripts/github/run_act_workflows.sh $(ARGS)

actions-local-list:
	@command -v act >/dev/null 2>&1 || (echo "act is not installed. See https://github.com/nektos/act#installation" && exit 1)
	@test -n "$(WORKFLOW)" || (echo "Usage: make actions-local-list WORKFLOW=test.yml" && exit 1)
	act --list -W .github/workflows/$(WORKFLOW)

lint: lint-backend lint-frontend

lint-imported: lint-data-management-frontend lint-scraper lint-embedding-modal lint-model-modal

lint-fix: lint-fix-backend lint-fix-frontend lint-fix-data-management-frontend

lint-backend:
	cd backend && uv run ruff check src tests

# Runs Black first so CI parity with GitHub (black --check src tests scripts) is fixed even if only lint-fix is used.
lint-fix-backend: format-backend
	cd backend && uv run ruff check --fix src tests

lint-frontend:
	cd frontend && npm run lint

lint-fix-frontend:
	cd frontend && npm run lint:fix

lint-data-management-frontend:
	cd apps/data-management-frontend && npm run lint

lint-fix-data-management-frontend:
	cd apps/data-management-frontend && npm run lint:fix

lint-scraper:
	cd services/scraper && make lint

lint-embedding-modal:
	cd services/embedding-modal && make lint

lint-model-modal:
	cd services/model-modal && make lint

typecheck: typecheck-backend typecheck-frontend

typecheck-imported: typecheck-scraper

typecheck-backend:
	cd backend && uv run mypy src

typecheck-frontend:
	cd frontend && npm run typecheck

typecheck-scraper:
	cd services/scraper && make type-check

format: format-backend format-frontend

format-backend:
	cd backend && uv run black --config pyproject.toml src tests scripts ../scripts/dm_openapi_diff.py

format-frontend:
	cd frontend && npm run format:write

format-check: format-check-backend format-check-frontend

format-check-backend:
	cd backend && uv run black --check --config pyproject.toml src tests scripts ../scripts/dm_openapi_diff.py

format-check-frontend:
	cd frontend && npm run format

audit: audit-backend audit-frontend

audit-backend:
	@set -e; \
	req=$$(mktemp); \
	trap 'rm -f "$$req"' EXIT; \
	cd backend && \
	uv export --frozen --format requirements.txt --no-hashes --no-annotate --no-header \
		--extra ci --no-emit-project -o "$$req" && \
	uv run --with pip-audit pip-audit -r "$$req" --progress-spinner off --desc

audit-frontend:
	cd frontend && npm audit --audit-level=high

audit-imported: audit-data-management-frontend

audit-data-management-frontend:
	cd apps/data-management-frontend && npm audit --audit-level=high

audit-fix: audit-fix-frontend audit-fix-data-management-frontend

audit-fix-frontend:
	cd frontend && npm audit fix

audit-fix-data-management-frontend:
	cd apps/data-management-frontend && npm audit fix

check-data-management-api-layout:
	test -d services/data-management-api/apps/backend
	test -d services/data-management-api/packages/shared-config

test-imported: check-data-management-api-layout test-data-management-frontend test-embedding-modal test-model-modal test-scraper

test-data-management-frontend:
	cd apps/data-management-frontend && npm run test

test-embedding-modal:
	cd services/embedding-modal && make test

test-model-modal:
	cd services/model-modal && make test

test-scraper:
	cd services/scraper && make test

quality-imported: lint-imported typecheck-imported audit-imported

quality: format-check lint typecheck audit quality-imported

quality-fix: format lint-fix audit-fix quality

# Sequential chain: stop on first failure (avoids parallel -j running later stages early).
quality-full:
	@$(MAKE) quality && $(MAKE) test-unit && $(MAKE) test-imported && $(MAKE) test-integration-gateway-fast && $(MAKE) test-integration-service-contracts

ci: quality-full

test-unit: test-backend-unit test-frontend-unit

test-backend-unit:
	cd backend && uv run pytest tests/ -m "unit and not llm" -v --tb=short && \
		PYTHONPATH=../services/data-management-api/packages/service-clients:../services/data-management-api/packages/shared-schemas:../services/data-management-api/packages/shared-config \
		uv run pytest \
			../services/data-management-api/packages/service-clients/tests/ \
			../services/data-management-api/tests/parity/ \
			-q --tb=short

test-frontend-unit:
	cd frontend && npm run test:unit

test-integration: test-all-integration test-cross-integration

test-integration-gateway-fast:
	cd backend && uv run pytest tests/integration/test_gateway_v1_matrix_coverage.py -q

# Matches GitHub Actions backend-integration job (service integration point contracts).
test-integration-service-contracts:
	cd backend && uv run pytest tests/integration/test_service_integration_points_contract.py -m "integration and not db and not llm" -v --tb=short

test-integration-gateway-full:
	cd backend && uv run pytest tests/integration -m "integration" \
		-k "gateway or streaming or modal_reindex or admin_tags" -v --tb=short

test-integration-gateway: test-integration-gateway-full

test-all-integration:
	cd backend && uv run pytest tests/ -m "integration and not llm" -v --tb=short

test-cross-integration:
	cd tests && uv run pytest -v -m integration

scraper-run:
	./scripts/run_scraper_postgres_batch.sh --local

scraper-pull:
	./scripts/sync_scraper_submodule.sh

scraper-run-verbose:
	./scripts/run_scraper_postgres_batch.sh --local --verbose

scraper-run-clean:
	./scripts/run_scraper_postgres_batch.sh --local --clean

scraper-validate-postgres:
	./scripts/run_scraper_postgres_batch.sh --skip-scraper

render-env-validate:
	python3 scripts/github/validate_render_env.py $(or $(ENV_FILE),.env.prod.render)

render-tests-strict:
	@echo "No strict-mode routing suite remains; skipping."

render-tests-render-suite:
	cd backend && uv run pytest tests/test_utils/test_render_env_contract.py tests/test_utils/test_service_endpoints.py tests/integration/test_service_integration_points_contract.py -q

render-workflow-ci: render-env-validate render-tests-render-suite

render-local-up:
	docker compose -f docker-compose.render-local.yml up -d --build

render-local-down:
	docker compose -f docker-compose.render-local.yml down -v --remove-orphans

render-local-logs:
	docker compose -f docker-compose.render-local.yml logs -f

render-local-check:
	@set -e; \
		env_file="$(or $(ENV_FILE),.env.prod.render)"; \
		temp_env_created=0; \
		if [ ! -f .env.render-local ]; then \
			cp "$$env_file" .env.render-local; \
			temp_env_created=1; \
			echo "[render-local-check] Bootstrapped temporary .env.render-local from $$env_file"; \
		fi; \
		echo "[render-local-check] Preflight validation (env + compose config)"; \
		python3 scripts/github/validate_render_env.py "$$env_file"; \
		docker compose -f docker-compose.render-local.yml config >/dev/null; \
		if curl -fsS --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then \
			echo "[render-local-check] Local Render stack detected; running live checks"; \
			ENV_FILE="$$env_file" ./scripts/local-render-check.sh --skip-simulation; \
		else \
			echo "[render-local-check] Local Render stack is not running."; \
			echo "[render-local-check] Run 'make render-local-up' then 'make render-local-check-live' for live probes."; \
			if [ "$$temp_env_created" = "1" ]; then rm -f .env.render-local; fi; \
			exit 0; \
		fi; \
		if [ "$$temp_env_created" = "1" ]; then rm -f .env.render-local; fi

render-local-check-live:
	ENV_FILE=$(or $(ENV_FILE),.env.prod.render) ./scripts/local-render-check.sh --skip-simulation

render-local-validate:
	@set -e; \
		env_file="$(or $(ENV_FILE),.env.prod.render)"; \
		temp_env_created=0; \
		if [ ! -f .env.render-local ]; then \
			cp "$$env_file" .env.render-local; \
			temp_env_created=1; \
		fi; \
		python3 scripts/github/validate_render_env.py "$$env_file"; \
		docker compose -f docker-compose.render-local.yml config >/dev/null; \
		if [ "$$temp_env_created" = "1" ]; then rm -f .env.render-local; fi; \
		echo "Render local preflight OK (env contract + compose config)"

env-sync-contract:
	@echo "Env sync contract target retired with routing decommissioning."

render-connectivity-tests:
	@echo "Running Render connectivity configuration tests (offline)..."
	cd backend && uv run pytest tests/render/ -v --tb=short -m render_connectivity

render-all-offline-contract-tests: env-sync-contract render-connectivity-tests
	@echo "All offline contract tests passed."

render-deploy-trigger:
	@echo "Triggering Render production deploy hooks (requires RENDER_*_DEPLOY_HOOK_URL env vars)..."
	@if [ -z "$(RENDER_AGENT_DEPLOY_HOOK_URL)" ] && [ -z "$(RENDER_GATEWAY_DEPLOY_HOOK_URL)" ]; then \
		echo "No deploy hook URLs set. Export RENDER_AGENT_DEPLOY_HOOK_URL, RENDER_GATEWAY_DEPLOY_HOOK_URL, RENDER_FRONTEND_DEPLOY_HOOK_URL."; \
		exit 1; \
	fi
	@[ -n "$(RENDER_AGENT_DEPLOY_HOOK_URL)" ] && curl -fsSL -X POST "$(RENDER_AGENT_DEPLOY_HOOK_URL)" && echo "Agent deploy triggered" || true
	@[ -n "$(RENDER_GATEWAY_DEPLOY_HOOK_URL)" ] && curl -fsSL -X POST "$(RENDER_GATEWAY_DEPLOY_HOOK_URL)" && echo "Gateway deploy triggered" || true
	@[ -n "$(RENDER_FRONTEND_DEPLOY_HOOK_URL)" ] && curl -fsSL -X POST "$(RENDER_FRONTEND_DEPLOY_HOOK_URL)" && echo "Frontend deploy triggered" || true

render-deploy-wait:
	@echo "Waiting for Render service to reach live status (requires RENDER_API_KEY and SERVICE_ID)..."
	python3 scripts/github/wait_for_render_deploy.py "$(SERVICE_ID)" --timeout $(or $(TIMEOUT),900)

# SERVICE_ID for targets below: Makefile SERVICE_ID=, or env RENDER_SERVICE_ID / RENDER_GATEWAY_SERVICE_ID.
render-services:
	@command -v python3 >/dev/null 2>&1 || (echo "python3 is required" && exit 1)
	python3 scripts/github/render_inspect.py services --limit $(or $(LIMIT),50)

render-deploy-status:
	@command -v python3 >/dev/null 2>&1 || (echo "python3 is required" && exit 1)
	@svc="$(or $(SERVICE_ID),$(RENDER_SERVICE_ID),$(RENDER_GATEWAY_SERVICE_ID))"; \
	if [ -z "$$svc" ]; then \
		echo "Usage: make render-deploy-status SERVICE_ID=srv-...  (or export RENDER_SERVICE_ID / RENDER_GATEWAY_SERVICE_ID)"; \
		exit 1; \
	fi; \
	python3 scripts/github/render_inspect.py deploys --service-id "$$svc" --limit $(or $(LIMIT),15)

render-deploy-show:
	@command -v python3 >/dev/null 2>&1 || (echo "python3 is required" && exit 1)
	@test -n "$(DEPLOY)" || (echo "Usage: make render-deploy-show DEPLOY=dep-... [SERVICE_ID=srv-...]" && exit 1)
	@svc="$(or $(SERVICE_ID),$(RENDER_SERVICE_ID),$(RENDER_GATEWAY_SERVICE_ID))"; \
	if [ -z "$$svc" ]; then \
		echo "Set SERVICE_ID or RENDER_SERVICE_ID / RENDER_GATEWAY_SERVICE_ID"; \
		exit 1; \
	fi; \
	python3 scripts/github/render_inspect.py deploy --service-id "$$svc" --deploy-id "$(DEPLOY)"

render-service-env:
	@command -v python3 >/dev/null 2>&1 || (echo "python3 is required" && exit 1)
	@svc="$(or $(SERVICE_ID),$(RENDER_SERVICE_ID),$(RENDER_GATEWAY_SERVICE_ID))"; \
	if [ -z "$$svc" ]; then \
		echo "Usage: make render-service-env SERVICE_ID=srv-...  (or export RENDER_SERVICE_ID / RENDER_GATEWAY_SERVICE_ID)"; \
		exit 1; \
	fi; \
	python3 scripts/github/render_inspect.py env --service-id "$$svc"

render-logs:
	@command -v python3 >/dev/null 2>&1 || (echo "python3 is required" && exit 1)
	@svc="$(or $(SERVICE_ID),$(RENDER_SERVICE_ID),$(RENDER_GATEWAY_SERVICE_ID))"; \
	if [ -z "$$svc" ]; then \
		echo "Usage: make render-logs SERVICE_ID=srv-... [LOG_TYPE=build] [LIMIT=80]"; \
		exit 1; \
	fi; \
	if [ -n "$(LOG_TYPE)" ]; then \
		python3 scripts/github/render_inspect.py logs --service-id "$$svc" --limit $(or $(LIMIT),80) --type "$(LOG_TYPE)"; \
	else \
		python3 scripts/github/render_inspect.py logs --service-id "$$svc" --limit $(or $(LIMIT),80); \
	fi

microservices-up:
	docker compose -f docker-compose.microservices.yml up -d

microservices-down:
	docker compose -f docker-compose.microservices.yml down -v --remove-orphans

microservices-logs:
	docker compose -f docker-compose.microservices.yml logs -f

test-microservices-contracts:
	cd tests && REQUIRE_MICROSERVICES=1 uv run pytest integration/test_microservices_contracts.py -v

test-microservices:
	@set -e; \
		docker compose -f docker-compose.microservices.yml up -d; \
		cd tests && REQUIRE_MICROSERVICES=1 uv run pytest integration/test_microservices_contracts.py -v; \
		docker compose -f ../docker-compose.microservices.yml down -v --remove-orphans

test-e2e: test-cross-e2e test-frontend-e2e

test-cross-e2e:
	cd tests && uv run pytest -v -m e2e

test-schemathesis-gateway:
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest tests/integration/test_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-gateway-pytest.html \
		--tracecov-fail-under=100

test-schemathesis-gateway-stateful:
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_gateway_scrape_stateful.py \
		tests/integration/test_gateway_modal_jobs_stateful.py -q

test-schemathesis-agent:
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest tests/integration/test_agent_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-agent-pytest.html \
		--tracecov-fail-under=100

test-schemathesis-data-management:
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_data_management_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-data-management-pytest.html \
		--tracecov-fail-under=100 \
		--junit-xml=schema-test-results-data-management.xml

test-schemathesis:
	@# One OpenAPI per TraceCov session (see tests/integration/conftest.py); run suites separately.
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-gateway-pytest.html \
		--tracecov-fail-under=100 \
		--junit-xml=schema-test-results-gateway.xml
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_agent_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-agent-pytest.html \
		--tracecov-fail-under=100 \
		--junit-xml=schema-test-results-agent.xml
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_data_management_api_schema_schemathesis.py -q \
		--tracecov-format=html,text \
		--tracecov-report-html-path=schema-coverage-data-management-pytest.html \
		--tracecov-fail-under=100 \
		--junit-xml=schema-test-results-data-management.xml

test-schemathesis-cli:
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	cd backend && bash scripts/run_schemathesis_live.sh

test-schemathesis-cli-agent:
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	cd backend && SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest tests/live/test_live_schemathesis.py -m live -q

# FR-005 / C1 (T032): assertable gateway + agent Schemathesis pytest entrypoints (TraceCov 100).
test-fr005-schemathesis-baseline: test-schemathesis-gateway test-schemathesis-agent

# FR-004 / SC-002: drift gate for committed DM OpenAPI snapshot (network to DATA_MANAGEMENT_SCHEMA_URL or default).
dm-openapi-diff:
	python3 scripts/dm_openapi_diff.py

# FR-007 / FR-008: Pact provider replay (skips unless env vars + generated pacts exist).
pact-verify-providers:
	cd backend && uv run pytest tests/pact/test_chat_gateway_provider_verify.py tests/pact/test_dm_api_provider_verify.py tests/pact/test_agent_provider_verify.py -q

test-frontend-e2e:
	cd frontend && npm run test:e2e

docs-install:
	cd website && npm ci

docs-serve:
	cd website && npm run start

docs-build:
	cd website && npm run build

docs-deploy-check: docs-build

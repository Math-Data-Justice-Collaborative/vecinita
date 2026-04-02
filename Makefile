.PHONY: help \
	dev dev-tmux dev-attach dev-stop dev-clear-ports \
	dev-chat dev-chat-backend dev-chat-gateway dev-chat-frontend \
	dev-data-management dev-data-management-frontend dev-data-management-api \
	dev-backend dev-gateway dev-frontend \
	branch-status branch-save branch-restore branch-switch branch-pull branch-sync-main \
	lint lint-backend lint-frontend lint-imported \
	typecheck typecheck-backend typecheck-frontend typecheck-imported \
	format format-backend format-frontend format-check format-check-backend format-check-frontend \
	quality quality-imported \
	test-unit test-integration test-e2e \
	test-backend-unit test-frontend-unit test-frontend-e2e \
	test-imported test-data-management-frontend test-modal-proxy test-embedding-modal test-model-modal test-scraper check-data-management-api-layout \
	lint-data-management-frontend lint-scraper lint-embedding-modal lint-model-modal \
	typecheck-scraper \
	test-integration-gateway-fast test-integration-gateway-full test-integration-gateway \
	test-all-integration test-cross-integration test-cross-e2e \
	microservices-up microservices-down microservices-logs test-microservices-contracts test-microservices \
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
	@echo "Quality targets"
	@echo "  make lint                                Lint core and imported codebases"
	@echo "  make lint-imported                       Lint imported service/frontend sub-repos"
	@echo "  make lint-backend                        Run Ruff checks"
	@echo "  make lint-frontend                       Run ESLint checks"
	@echo "  make typecheck                           Type-check core and imported codebases"
	@echo "  make typecheck-imported                  Run imported sub-repo type checks"
	@echo "  make typecheck-backend                   Run mypy on backend source"
	@echo "  make typecheck-frontend                  Run TypeScript checks"
	@echo "  make format                              Format backend and frontend"
	@echo "  make format-backend                      Format backend with Black"
	@echo "  make format-frontend                     Format frontend with Prettier"
	@echo "  make format-check                        Check formatting without writing"
	@echo "  make quality-imported                    Run imported sub-repo checks"
	@echo "  make quality                             Run core + imported quality checks + fast integration"
	@echo ""
	@echo "Testing targets"
	@echo "  make test-unit                           Run backend and frontend unit tests"
	@echo "  make test-backend-unit                   Run backend unit tests"
	@echo "  make test-frontend-unit                  Run frontend unit tests"
	@echo "  make test-imported                       Run imported sub-repo test suites"
	@echo "  make test-integration                    Run backend and cross-stack integration tests"
	@echo "  make test-integration-gateway-fast       Run gateway matrix contract checks"
	@echo "  make test-integration-gateway-full       Run gateway-focused integration suites"
	@echo "  make test-integration-gateway            Alias of full gateway integration"
	@echo "  make test-all-integration                Run all backend integration tests"
	@echo "  make test-cross-integration              Run tests/ integration suite"
	@echo "  make test-microservices-contracts        Run proxy/model/embedding/scraper contract tests"
	@echo "  make test-microservices                  Start stack, run contracts, stop stack"
	@echo "  make test-e2e                            Run frontend and cross-stack e2e tests"
	@echo "  make test-cross-e2e                      Run tests/ e2e suite"
	@echo "  make test-frontend-e2e                   Run frontend Playwright tests"
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
	@for port in 5173 5174 8000 8001 8002 8004 8005; do \
		pids="$$( (command -v lsof >/dev/null 2>&1 && lsof -ti tcp:$$port 2>/dev/null) || (command -v fuser >/dev/null 2>&1 && fuser -n tcp $$port 2>/dev/null) || true )"; \
		if [ -n "$$pids" ]; then \
			echo "Clearing port $$port (PID(s): $$pids)"; \
			kill -9 $$pids 2>/dev/null || true; \
		else \
			echo "Port $$port already free"; \
		fi; \
	done

dev-backend:
	cd backend && CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' \
		uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc'

dev-gateway:
	cd backend && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='http://localhost:8001' \
		CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' \
		SUPABASE_URL='http://localhost:3001' SUPABASE_KEY='test-anon-key-local-development-only' \
		DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' \
		SUPABASE_UPLOADS_BUCKET='documents' DEMO_MODE='false' \
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
	@cd backend && CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' \
		uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc' &

dev-chat-gateway:
	@echo "Starting Chat Gateway (port 8004, Supabase-enabled)..."
	@cd backend && source ../.env && \
		AGENT_SERVICE_URL='http://localhost:8000' \
		EMBEDDING_SERVICE_URL='http://localhost:8001' \
		CHROMA_HOST='localhost' \
		CHROMA_PORT='8002' \
		CHROMA_SSL='false' \
		DEV_ADMIN_ENABLED='true' \
		DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' \
		uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc' &

dev-chat-frontend:
	@echo "Starting Chat Frontend (port 5173, Supabase-enabled)..."
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
	@echo "Starting Data Management API (port 8005, Supabase-enabled)..."
	@test -d services/data-management-api/apps/backend/proxy/app || \
		(echo "❌ data-management-api submodule not initialized." && \
		 echo "   Run: git submodule update --init services/data-management-api" && exit 1)
	@cd services/data-management-api/apps/backend/proxy && \
		source ../../../../../.env && \
		PORT=8005 uv run uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload &
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

lint: lint-backend lint-frontend

lint-imported: lint-data-management-frontend lint-scraper lint-embedding-modal lint-model-modal

lint-backend:
	cd backend && uv run ruff check src tests

lint-frontend:
	cd frontend && npm run lint

lint-data-management-frontend:
	cd apps/data-management-frontend && npm run lint

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
	cd backend && uv run black src tests

format-frontend:
	cd frontend && npm run format:write

format-check: format-check-backend format-check-frontend

format-check-backend:
	cd backend && uv run black --check src tests

format-check-frontend:
	cd frontend && npm run format

check-data-management-api-layout:
	test -d services/data-management-api/apps/backend
	test -d services/data-management-api/packages/shared-config

test-imported: check-data-management-api-layout test-data-management-frontend test-modal-proxy test-embedding-modal test-model-modal test-scraper

test-data-management-frontend:
	cd apps/data-management-frontend && npm run test

test-modal-proxy:
	cd services/modal-proxy && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=95

test-embedding-modal:
	cd services/embedding-modal && make test

test-model-modal:
	cd services/model-modal && make test

test-scraper:
	cd services/scraper && make test

quality-imported: lint-imported typecheck-imported test-imported

quality: lint typecheck format-check test-unit quality-imported test-integration-gateway-fast

test-unit: test-backend-unit test-frontend-unit

test-backend-unit:
	cd backend && uv run pytest tests/ -m "unit and not llm" -v --tb=short

test-frontend-unit:
	cd frontend && npm run test:unit

test-integration: test-all-integration test-cross-integration

test-integration-gateway-fast:
	cd backend && uv run pytest tests/integration/test_gateway_v1_matrix_coverage.py -q

test-integration-gateway-full:
	cd backend && uv run pytest tests/integration -m "integration" \
		-k "gateway or streaming or modal_reindex or admin_tags" -v --tb=short

test-integration-gateway: test-integration-gateway-full

test-all-integration:
	cd backend && uv run pytest tests/ -m "integration and not llm" -v --tb=short

test-cross-integration:
	cd tests && uv run pytest -v -m integration

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

test-frontend-e2e:
	cd frontend && npm run test:e2e

docs-install:
	cd website && npm ci

docs-serve:
	cd website && npm run start

docs-build:
	cd website && npm run build

docs-deploy-check: docs-build

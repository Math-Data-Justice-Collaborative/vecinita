.PHONY: help \
	dev dev-tmux dev-attach dev-stop dev-clear-ports dev-backend dev-gateway dev-frontend \
	lint lint-backend lint-frontend \
	typecheck typecheck-backend typecheck-frontend \
	format format-backend format-frontend \
	test-unit test-integration test-e2e \
	test-backend-unit test-frontend-unit test-frontend-e2e \
	test-integration-gateway-fast test-integration-gateway-full test-integration-gateway \
	test-all-integration test-cross-integration test-cross-e2e \
	docs-install docs-serve docs-build docs-deploy-check

help:
	@echo "Vecinita root Makefile"
	@echo ""
	@echo "Development targets"
	@echo "  make dev                            Start full local dev stack with cascading logs"
	@echo "  make dev-tmux                       Start the legacy tmux split-pane dev session"
	@echo "  make dev-attach                     Attach to the existing tmux dev session"
	@echo "  make dev-stop                       Stop the dev session and local containers"
	@echo "  make dev-clear-ports                Kill processes bound to local dev ports"
	@echo "  make dev-backend                    Start the backend agent in reload mode"
	@echo "  make dev-gateway                    Start the API gateway in reload mode"
	@echo "  make dev-frontend                   Start the frontend dev server"
	@echo ""
	@echo "Quality targets"
	@echo "  make lint                           Lint backend and frontend"
	@echo "  make lint-backend                   Run Ruff checks"
	@echo "  make lint-frontend                  Run ESLint checks"
	@echo "  make typecheck                      Type-check backend and frontend"
	@echo "  make typecheck-backend              Run mypy on backend source"
	@echo "  make typecheck-frontend             Run TypeScript checks"
	@echo "  make format                         Format backend and frontend"
	@echo "  make format-backend                 Format backend with Black"
	@echo "  make format-frontend                Format frontend with Prettier"
	@echo ""
	@echo "Testing targets"
	@echo "  make test-unit                      Run backend and frontend unit tests"
	@echo "  make test-backend-unit              Run backend unit tests"
	@echo "  make test-frontend-unit             Run frontend unit tests"
	@echo "  make test-integration               Run backend and cross-stack integration tests"
	@echo "  make test-integration-gateway-fast  Run gateway matrix contract checks"
	@echo "  make test-integration-gateway-full  Run gateway-focused integration suites"
	@echo "  make test-integration-gateway       Alias of full gateway integration"
	@echo "  make test-all-integration           Run all backend integration tests"
	@echo "  make test-cross-integration         Run tests/ integration suite"
	@echo "  make test-e2e                       Run frontend and cross-stack e2e tests"
	@echo "  make test-cross-e2e                 Run tests/ e2e suite"
	@echo "  make test-frontend-e2e              Run frontend Playwright tests"
	@echo ""
	@echo "Documentation targets"
	@echo "  make docs-install                   Install Docusaurus dependencies"
	@echo "  make docs-serve                     Start docs site locally"
	@echo "  make docs-build                     Build docs site"
	@echo "  make docs-deploy-check              Validate docs build for Pages"

dev:
	./run/dev-session.sh start

dev-tmux:
	./run/dev-session.sh start-tmux

dev-attach:
	./run/dev-session.sh attach

dev-stop:
	./run/dev-session.sh stop

dev-clear-ports:
	@for port in 5173 8000 8001 8002 8004; do \
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
		uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload

dev-gateway:
	cd backend && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='http://localhost:8001' \
		CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' \
		SUPABASE_URL='http://localhost:3001' SUPABASE_KEY='test-anon-key-local-development-only' \
		DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' \
		SUPABASE_UPLOADS_BUCKET='documents' DEMO_MODE='false' \
		uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload

dev-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check src tests

lint-frontend:
	cd frontend && npm run lint

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd backend && uv run mypy src

typecheck-frontend:
	cd frontend && npm run typecheck

format: format-backend format-frontend

format-backend:
	cd backend && uv run black src tests

format-frontend:
	cd frontend && npm run format:write

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

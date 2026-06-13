# Vecinita monorepo — local dev and CI-parity checks.
# Run `make help` for targets.

.DEFAULT_GOAL := help

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

UV := uv
PYTHON_DIRS := apps packages tests
PYTEST_DEFAULT := tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
COMPOSE_FILE := infra/docker-compose.yml
DATABASE_URL ?= postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
export DATABASE_URL

FRONTENDS := chat-rag-frontend data-management-frontend

.PHONY: help install \
	db-up db-wait db-ready db-down migrate \
	lint lint-py lint-fe \
	format format-check \
	typecheck typecheck-py typecheck-fe \
	test test-py test-fe test-unit test-integration test-e2e test-smoke test-privacy test-live \
	build-frontend ci ci-guards audit audit-fe audit-fix check

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make install          # uv sync + npm ci (both frontends)"
	@echo "  make check            # lint + format-check + typecheck"
	@echo "  make audit            # pip-audit (Python, with ignore list)"
	@echo "  make audit-fix        # auto-fix CVEs, re-audit, then make check"
	@echo "  make test             # full Python suite + frontend Vitest"
	@echo "  make ci               # CI-parity (guards, audit, tests, frontend build)"

install: ## Install Python (uv) and frontend (npm ci) dependencies
	$(UV) sync --group dev
	@for app in $(FRONTENDS); do \
		echo "==> npm ci apps/$$app"; \
		(cd apps/$$app && npm ci); \
	done

db-up: ## Start local Postgres (docker compose)
	docker compose -f $(COMPOSE_FILE) up -d postgres

db-wait: ## Wait until Postgres accepts connections
	@echo "Waiting for Postgres..."
	@until docker compose -f $(COMPOSE_FILE) exec -T postgres pg_isready -U vecinita -d vecinita >/dev/null 2>&1; do sleep 1; done

db-ready: db-up db-wait ## Start Postgres and wait until ready

db-down: ## Stop local Postgres
	docker compose -f $(COMPOSE_FILE) down

migrate: db-ready ## Apply Alembic migrations
	cd apps/database && $(UV) run alembic upgrade head

lint-py: ## Ruff lint (Python)
	$(UV) run ruff check $(PYTHON_DIRS)

lint-fe: ## ESLint (both frontends)
	@for app in $(FRONTENDS); do \
		echo "==> npm run lint apps/$$app"; \
		(cd apps/$$app && npm run lint); \
	done

lint: lint-py lint-fe ## Lint Python + both frontends (fail fast)

format-check: ## Check Python formatting (ruff, no writes)
	$(UV) run ruff format --check $(PYTHON_DIRS)

format: ## Fix Python formatting (ruff)
	$(UV) run ruff format $(PYTHON_DIRS)

typecheck-py: ## basedpyright (Python)
	$(UV) run basedpyright $(PYTHON_DIRS)

typecheck-fe: ## tsc --noEmit (both frontends)
	@echo "==> tsc apps/chat-rag-frontend"
	cd apps/chat-rag-frontend && npx tsc --noEmit
	@echo "==> tsc apps/data-management-frontend"
	cd apps/data-management-frontend && npx tsc -p tsconfig.build.json --noEmit

typecheck: typecheck-py typecheck-fe ## Typecheck Python + both frontends (fail fast)

test-unit: ## Pytest unit tests
	$(UV) run pytest tests/unit

test-integration: migrate ## Pytest integration tests (starts DB + migrates)
	$(UV) run pytest tests/integration

test-e2e: migrate ## Pytest local E2E user journeys (starts DB + migrates)
	$(UV) run pytest tests/e2e -m "e2e and not live"

test-smoke: migrate ## Pytest smoke tests (starts DB + migrates)
	$(UV) run pytest tests/smoke -m "not live"

test-privacy: migrate ## Pytest privacy guardrail tests (starts DB + migrates)
	$(UV) run pytest tests/privacy

test-py: migrate ## Full Python test suite (matches CI pytest paths)
	$(UV) run pytest $(PYTEST_DEFAULT)

test-fe: ## Vitest (both frontends)
	@for app in $(FRONTENDS); do \
		echo "==> npm test apps/$$app"; \
		(cd apps/$$app && npm test); \
	done

test: test-py test-fe ## Full test suite: Python + frontends (fail fast)

test-live: ## Live staging smokes (requires VECINITA_STAGING_* env vars)
	$(UV) run pytest tests/smoke -m live -v

build-frontend: ## Production build (both frontends)
	@for app in $(FRONTENDS); do \
		echo "==> npm run build apps/$$app"; \
		(cd apps/$$app && npm run build); \
	done

ci-guards: ## CI static guard scripts (secrets, OpenAPI, Modal boundary)
	bash scripts/check_modal_no_database_url.sh
	bash scripts/check_openapi_specs.sh
	bash scripts/check_secrets.sh
	bash scripts/check_no_operator_specs_tracked.sh
	@if command -v gitleaks >/dev/null 2>&1; then \
		gitleaks detect --no-git --config .gitleaks.toml; \
	else \
		echo "skip: gitleaks not installed (install v8.24.2+ for full CI parity)"; \
	fi

audit: ## pip-audit with repo ignore list (blocking in CI)
	@IGNORE_ARGS=(); \
	while read -r cve; do \
		[[ -z "$$cve" || "$$cve" =~ ^# ]] && continue; \
		IGNORE_ARGS+=(--ignore-vuln "$$cve"); \
	done < audit/pip-audit-ignore.txt; \
	$(UV) run pip-audit "$${IGNORE_ARGS[@]}"

audit-fe: ## npm audit (both frontends)
	@for app in $(FRONTENDS); do \
		echo "==> npm audit apps/$$app"; \
		(cd apps/$$app && npm audit); \
	done

audit-fix: ## Auto-fix dependency CVEs (Python + frontends), then verify
	@echo "==> pip-audit --fix (Python, no ignore list)"
	$(UV) run pip-audit --fix
	$(UV) lock
	$(UV) sync
	@for app in $(FRONTENDS); do \
		echo "==> npm audit fix apps/$$app"; \
		(cd apps/$$app && npm audit fix); \
	done
	$(MAKE) audit
	$(MAKE) audit-fe
	$(MAKE) check

check: lint format-check typecheck ## Quick pre-push: lint + format-check + typecheck

ci: install ci-guards lint format-check typecheck audit test-py test-fe build-frontend ## Full CI-parity run (fail fast)

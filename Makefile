# Vecinita monorepo — local dev and CI-parity checks.
# Run `make help` for targets.

.DEFAULT_GOAL := help

SHELL := /bin/bash
.SHELLFLAGS := --noprofile --norc -eu -o pipefail -c

UV := uv
PYTHON_DIRS := apps packages tests infra scripts
PYTEST_DEFAULT := tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
COMPOSE_FILE := infra/docker-compose.yml
DATABASE_URL ?= postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
export DATABASE_URL
WITH_POSTGRES := bash scripts/ci/with_local_postgres.sh

FRONTENDS := chat-rag-frontend data-management-frontend
FE_WORKSPACES := vecinita-frontend-i18n vecinita-frontend-ui \
	vecinita-chat-rag-frontend vecinita-data-management-frontend
NPM_LOCK := bash scripts/npm_with_lock.sh
NPM_WS := bash scripts/npm_workspaces.sh

.PHONY: help install \
	db-up db-wait db-ready db-down migrate migrate-only \
	lint lint-py lint-fe lint-fix lint-fix-py lint-fix-fe \
	format format-py format-fe format-check format-check-py format-fe-check \
	typecheck typecheck-py typecheck-fe \
	test test-py test-fe test-ui test-unit test-unit-coverage test-fast test-coverage-fe test-integration test-e2e test-smoke test-privacy test-live \
	verify-connectivity \
	build-frontend ci ci-push ci-push-py ci-pr-ready ci-guards audit audit-fe audit-fix 	check check-fast pre-push

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make install          # uv sync + npm ci (both frontends)"
	@echo "  make check            # lint + format-check + typecheck"
	@echo "  make check-fast       # lint + typecheck only (agent stop + pre-push hook)"
	@echo "  make pre-push         # same as Husky pre-push (check-fast + test-fast)"
	@echo "  make test-fast        # unit tests for locally changed components"
	@echo "  make ci-push          # full CI parity — run before opening a PR"
	@echo "  make ci-pr-ready      # alias for ci-push"
	@echo "  make audit            # pip-audit (Python, with ignore list)"
	@echo "  make audit-fix        # auto-fix CVEs, re-audit, then make check"
	@echo "  make test             # full Python suite + frontend Vitest"
	@echo "  make test-unit-coverage  # unit tests + per-package/app coverage summary"
	@echo "  make ci               # CI-parity (guards, audit, tests, frontend build)"

install: ## Install Python (uv) and frontend (npm ci) dependencies
	@$(NPM_LOCK) bash -eu -o pipefail -c '$(UV) sync --group dev; $(NPM_WS) install'

db-up: ## Start local Postgres (docker compose)
	docker compose -f $(COMPOSE_FILE) up -d postgres

db-wait: ## Wait until Postgres accepts connections
	@echo "Waiting for Postgres..."
	@until docker compose -f $(COMPOSE_FILE) exec -T postgres pg_isready -U vecinita -d vecinita >/dev/null 2>&1; do sleep 1; done

db-ready: db-up db-wait ## Start Postgres and wait until ready

db-down: ## Stop local Postgres
	docker compose -f $(COMPOSE_FILE) down

migrate: db-ready migrate-only ## Start Postgres and apply migrations

migrate-only: ## Apply Alembic migrations (Postgres must already be up)
	cd apps/database && $(UV) run alembic upgrade head

lint-py: ## Ruff lint (Python)
	$(UV) run ruff check $(PYTHON_DIRS)

lint-fe: ## ESLint (frontend apps + packages)
	@$(NPM_LOCK) $(NPM_WS) run lint $(FE_WORKSPACES)

lint: lint-py lint-fe ## Lint Python + frontends (fail fast)

lint-fix-py: ## Auto-fix Ruff lint (Python)
	$(UV) run ruff check --fix $(PYTHON_DIRS)

lint-fix-fe: ## Auto-fix ESLint (frontend apps + packages)
	@$(NPM_LOCK) bash -eu -o pipefail -c '$(NPM_WS) install; \
		for ws in $(FE_WORKSPACES); do \
			echo "==> eslint --fix -w $$ws"; \
			npm exec -w "$$ws" -- eslint src --fix; \
		done'

lint-fix: lint-fix-py lint-fix-fe ## Auto-fix lint (Python + both frontends)

format-check-py: ## Check Python formatting (ruff, no writes)
	$(UV) run ruff format --check $(PYTHON_DIRS)

format-py: ## Fix Python formatting (ruff)
	$(UV) run ruff format $(PYTHON_DIRS)

format-fe-check: ## Check frontend formatting (Prettier, no writes)
	@$(NPM_LOCK) $(NPM_WS) run 'format:check' $(FE_WORKSPACES)

format-fe: ## Fix frontend formatting (Prettier)
	@$(NPM_LOCK) $(NPM_WS) run 'format' $(FE_WORKSPACES)

format-check: format-check-py format-fe-check ## Check Python + frontend formatting

format: format-py format-fe ## Fix Python + frontend formatting

typecheck-py: ## basedpyright (Python)
	$(UV) run basedpyright $(PYTHON_DIRS)

typecheck-fe: ## tsc --noEmit (frontend apps + packages)
	@$(NPM_LOCK) $(NPM_WS) run typecheck $(FE_WORKSPACES)

typecheck: typecheck-py typecheck-fe ## Typecheck Python + both frontends (fail fast)

test-unit: ## Pytest unit tests
	$(UV) run pytest tests/unit

test-unit-coverage: ## Unit tests with per-package/app coverage summary (htmlcov/, coverage/)
	$(WITH_POSTGRES) bash scripts/test/unit_coverage.sh

test-fast: ## Unit tests for changed components only (fast agent feedback)
	bash scripts/ci/test_fast.sh

test-coverage-fe: ## Vitest coverage for one frontend (FE_APP=chat-rag-frontend|data-management-frontend)
	@test -n "$(FE_APP)" || (echo "Usage: make test-coverage-fe FE_APP=chat-rag-frontend" && exit 1)
	@$(NPM_LOCK) npm run test:coverage -w vecinita-$(FE_APP)

test-integration: ## Pytest integration tests (starts/stops compose postgres when needed)
	$(WITH_POSTGRES) $(UV) run pytest tests/integration

test-e2e: ## Pytest local E2E user journeys (starts/stops compose postgres when needed)
	$(WITH_POSTGRES) $(UV) run pytest tests/e2e -m "e2e and not live"

test-smoke: ## Pytest smoke tests (starts/stops compose postgres when needed)
	$(WITH_POSTGRES) $(UV) run pytest tests/smoke -m "not live"

test-privacy: ## Pytest privacy guardrail tests (starts/stops compose postgres when needed)
	$(WITH_POSTGRES) $(UV) run pytest tests/privacy

test-py: ## Full Python test suite (starts/stops compose postgres when needed)
	$(WITH_POSTGRES) $(UV) run pytest $(PYTEST_DEFAULT)

test-fe: ## Vitest (both frontends)
	@$(NPM_LOCK) $(NPM_WS) run test

test-ui: ## Playwright UI E2E (T0-ui — preview bundles + route mocks)
	bash scripts/ui/run_playwright.sh

test: test-py test-fe ## Full test suite: Python + frontends (fail fast)

test-live: ## Live staging smokes (requires VECINITA_STAGING_* env vars)
	$(UV) run pytest tests/smoke -m live -v

verify-connectivity: ## H0c + optional H4/H5 live (see infra/staging/.env.example)
	bash scripts/deploy/verify_connectivity.sh

build-frontend: ## Production build (both frontends)
	@$(NPM_LOCK) $(NPM_WS) run build

ci-guards: ## CI static guard scripts (secrets, OpenAPI, Modal boundary)
	bash scripts/check_modal_no_database_url.sh
	bash scripts/check_openapi_specs.sh
	bash scripts/check_supabase_config.sh
	bash scripts/check_secrets.sh
	bash scripts/check_no_operator_specs_tracked.sh
	bash scripts/check_corpus_reset_guard.sh
	bash scripts/check_do_required_secrets.sh
	bash scripts/check_doc_archive_paths.sh
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
	@$(NPM_LOCK) bash -eu -o pipefail -c 'for app in $(FRONTENDS); do \
		echo "==> npm audit apps/$$app"; \
		( cd apps/$$app && npm audit ); \
	done'

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

check: lint format-check typecheck ## Pre-commit: lint + format-check + typecheck

check-fast: lint typecheck ## Fast gate: lint + typecheck (no format-check; Husky pre-push)

pre-push: check-fast test-fast ## Husky pre-push tier (fast local gate before git push)

ci: install ci-guards lint format-check typecheck audit test-py test-fe build-frontend ## Full CI-parity run (fail fast)

ci-push: ci-guards lint format-check typecheck audit ci-push-py test-fe build-frontend ## Full CI parity before opening a PR (no reinstall)

ci-push-py: ## Python tests + unit coverage in one Postgres session (compose torn down if we started it)
	$(WITH_POSTGRES) bash scripts/ci/run_pytest_ci_push.sh

ci-pr-ready: ci-push ## Alias — run before marking a PR ready for review

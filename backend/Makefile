.PHONY: format format-check lint lint-fix typecheck audit test test-e2e quality quality-fix test-streaming-ci test-contracts test-acceptance-gateway-ask test-schema test-schema-cli

format:
	uv run black src tests

format-check:
	uv run black --check src tests

lint:
	uv run ruff check src

lint-fix:
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

audit:
	uv run --with pip-audit pip-audit --progress-spinner off --desc

test:
	uv run pytest -q

test-e2e:
	uv run pytest tests/e2e -v --tb=short

test-contracts:
	uv run pytest tests/integration/test_service_integration_points_contract.py tests/integration/test_service_integration_points_contract_expanded.py -q

test-acceptance-gateway-ask:
	uv run pytest tests/integration/test_gateway_ask_acceptance.py -q

test-schema:
	SCHEMATHESIS_HOOKS=tests.schemathesis_hooks uv run pytest \
		tests/integration/test_api_schema_schemathesis.py \
		tests/integration/test_agent_api_schema_schemathesis.py \
		-q

test-schema-cli:
	bash scripts/run_schemathesis_live.sh

quality: format-check lint typecheck audit

quality-fix: format lint-fix quality

test-streaming-ci:
	uv run pytest -m streaming -q \
		--ignore=tests/test_scraper_advanced.py \
		--ignore=tests/test_scraper_upload_chunks.py \
		--ignore=tests/test_services/scraper/test_scraper_advanced.py \
		--ignore=tests/test_services/scraper/test_scraper_upload_chunks.py

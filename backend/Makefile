.PHONY: format format-check lint typecheck test quality test-streaming-ci

format:
	uv run black src tests

format-check:
	uv run black --check src tests

lint:
	uv run ruff check src

typecheck:
	uv run mypy src

test:
	uv run pytest -q

quality: format-check lint typecheck test

test-streaming-ci:
	uv run pytest -m streaming -q \
		--ignore=tests/test_scraper_advanced.py \
		--ignore=tests/test_scraper_upload_chunks.py \
		--ignore=tests/test_services/scraper/test_scraper_advanced.py \
		--ignore=tests/test_services/scraper/test_scraper_upload_chunks.py

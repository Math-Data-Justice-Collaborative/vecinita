PYTHON ?= python3.11

.PHONY: lint test test-integration

lint:
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .

test:
	PYTHONPATH=src $(PYTHON) -m pytest

test-integration:
	PYTHONPATH=src $(PYTHON) -m pytest -m integration --no-cov

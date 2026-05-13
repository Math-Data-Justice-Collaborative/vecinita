.PHONY: help install dev-install lint format type-check test test-unit test-integration test-live test-cov clean deploy serve

PYTHON_BIN ?= $(shell command -v python3.11 >/dev/null 2>&1 && echo python3.11 || echo python3)
PYTHONWARNINGS ?= ignore:::requests

help:
	@echo "Vecinita Scraper Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install         - Install production dependencies"
	@echo "  make dev-install     - Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            - Run linter (ruff)"
	@echo "  make format          - Format code (black, isort)"
	@echo "  make type-check      - Run type checker (mypy)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests (unit + integration, exclude live)"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-live       - Run live API tests"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy          - Deploy to Modal"
	@echo "  make serve           - Serve locally with modal"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove build artifacts"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

test:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" pytest -m "not live" -v

test-unit:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" pytest tests/unit/ -v

test-integration:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" pytest tests/integration/ -v

test-live:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" pytest -m live -v || ([ $$? -eq 5 ] && echo "No live tests collected; treating as success.")

test-cov:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" pytest --cov=src/vecinita_scraper --cov-report=html --cov-report=term-missing

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov dist build .pytest_cache .mypy_cache

deploy:
	PYTHONPATH=src $(PYTHON_BIN) -m modal deploy src/vecinita_scraper/app.py
	PYTHONPATH=src $(PYTHON_BIN) -m modal deploy src/vecinita_scraper/api/app.py

serve:
	PYTHONPATH=src $(PYTHON_BIN) -m modal serve src/vecinita_scraper/api/app.py

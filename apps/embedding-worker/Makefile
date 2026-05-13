PYTHON ?= python3.11

.PHONY: lint test deploy serve

lint:
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest tests/

deploy:
	$(PYTHON) -m modal deploy main.py

serve:
	$(PYTHON) -m modal serve main.py

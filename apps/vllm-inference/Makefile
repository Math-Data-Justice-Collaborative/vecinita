.PHONY: lint test docker-up docker-down docker-logs docker-pull-model deploy warm-default-model deploy-and-warm verify-health

PYTHONWARNINGS ?= ignore:::requests

lint:
	ruff check .

test:
	PYTHONWARNINGS="$(PYTHONWARNINGS)" PYTHONPATH=src pytest

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api

docker-pull-model:
	docker compose exec ollama ollama pull gemma3

deploy:
	PYTHONPATH=src python3 -m modal deploy main.py

# Pull default Ollama weights into the shared Modal volume (same as CI after deploy).
warm-default-model:
	PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_default_model

deploy-and-warm: deploy warm-default-model

verify-health:
	curl -fsS "$$VECINITA_API_URL/health"
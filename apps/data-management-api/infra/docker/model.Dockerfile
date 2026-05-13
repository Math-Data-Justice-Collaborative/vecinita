# Repo-root-context build for vecinita-model.
# For standalone service-directory builds, use apps/backend/model-service/Dockerfile directly.
# This service requires an Ollama instance; set OLLAMA_HOST appropriately.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/model-service/pyproject.toml \
     apps/backend/model-service/README.md \
     /app/
COPY apps/backend/model-service/src /app/src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && pip install --no-cache-dir uvicorn

EXPOSE 8000

CMD ["uvicorn", "vecinita.asgi:app", "--host", "0.0.0.0", "--port", "8000"]

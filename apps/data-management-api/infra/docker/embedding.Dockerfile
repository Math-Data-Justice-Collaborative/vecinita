# vecinita-embedding is a Modal serverless service and is NOT run as a local container.
#
# To deploy to Modal:
#   cd apps/backend/embedding-service
#   pip install modal
#   modal deploy main.py
#
# To run locally with Modal:
#   modal serve main.py
#
# This Dockerfile installs dependencies for linting/testing purposes only.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/backend/embedding-service/pyproject.toml ./
COPY apps/backend/embedding-service/src ./src
COPY apps/backend/embedding-service/main.py \
     apps/backend/embedding-service/models.py \
     ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# No CMD: this service runs via Modal, not as a containerised process.
# See apps/backend/embedding-service/README.md for deployment instructions.

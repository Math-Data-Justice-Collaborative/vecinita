# syntax=docker/dockerfile:1
# Render builds with BuildKit. Heavy deps install against a minimal stub package; real `src/` is
# copied afterward so source-only edits invalidate only a cheap `pip install . --no-deps` layer.
# Base pin: docker.io/library/python:3.11-slim @ digest (update periodically for security patches).
FROM python@sha256:233de06753d30d120b1a3ce359d8d3be8bda78524cd8f520c99883bfe33964cf

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

COPY pyproject.toml README.md ./

# Minimal tree matching setuptools `where = ["src"]` so the first `pip install .` resolves deps.
RUN mkdir -p src/vecinita_scraper \
    && printf '%s\n' '"""Dependency-layer stub; replaced by COPY src."""' '__version__ = "0.0.0"' > src/vecinita_scraper/__init__.py

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

COPY src ./src

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --no-deps .

EXPOSE 10000

CMD ["sh", "-c", "uvicorn vecinita_scraper.api.server:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}"]

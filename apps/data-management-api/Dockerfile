FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Nested `apps/backend/scraper-service` submodules were removed (003-consolidate-scraper-dm).
# The vecinita **monorepo** builds production images from `services/scraper/` (see root `render.yaml`).
# Standalone clones of this repo fetch the same sources at build time:
ARG VECINITA_SCRAPER_REPO=https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper.git
ARG VECINITA_SCRAPER_REF=main
RUN git clone --depth 1 --branch "${VECINITA_SCRAPER_REF}" "${VECINITA_SCRAPER_REPO}" /tmp/vecinita-scraper \
    && cp /tmp/vecinita-scraper/pyproject.toml /tmp/vecinita-scraper/README.md /app/ \
    && cp -a /tmp/vecinita-scraper/src /app/src \
    && rm -rf /tmp/vecinita-scraper

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

CMD ["sh", "-c", "uvicorn vecinita_scraper.api.server:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}"]

# vecinita-scraper is primarily deployed via Modal or the vecinita monorepo `services/scraper` image.
# Nested `apps/backend/scraper-service` checkouts were removed — sources are fetched at build time.
#
# To deploy to Modal, use the vecinita-scraper repository (or monorepo `services/scraper`) directly.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG VECINITA_SCRAPER_REPO=https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper.git
ARG VECINITA_SCRAPER_REF=main
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 --branch "${VECINITA_SCRAPER_REF}" "${VECINITA_SCRAPER_REPO}" /tmp/vecinita-scraper \
    && cp /tmp/vecinita-scraper/pyproject.toml /app/ \
    && cp -a /tmp/vecinita-scraper/src /app/src \
    && rm -rf /tmp/vecinita-scraper

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# No CMD: Modal / local workflows use this image for tooling parity only.

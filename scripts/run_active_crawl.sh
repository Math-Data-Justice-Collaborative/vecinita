#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -z "${DATABASE_URL:-}" && -f "${REPO_ROOT}/.env" ]]; then
  DATABASE_URL="$(grep -E '^DATABASE_URL=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r')"
  export DATABASE_URL
fi
if [[ -z "${DATABASE_URL:-}" && -f "${REPO_ROOT}/.env" ]]; then
  DB_URL="$(grep -E '^DB_URL=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r')"
  export DB_URL
fi
if [[ -n "${DATABASE_URL:-}" ]]; then
  DATABASE_URL="${DATABASE_URL//$'\r'/}"
  export DATABASE_URL
fi

# Match backend/scripts/run_scraper.sh defaults so the Python environment matches
# the main scraper pipeline (embeddings HTTP client, etc.). LLM/tagging env vars
# still come from repo .env via python-dotenv in the active_crawl CLI; this export
# keeps EMBEDDING_SERVICE_URL consistent when chaining with make scraper-run.
if [[ -z "${EMBEDDING_SERVICE_URL:-}" && -f "${REPO_ROOT}/.env" ]]; then
  _emb="$(grep -E '^EMBEDDING_SERVICE_URL=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ -n "${_emb:-}" ]]; then
    export EMBEDDING_SERVICE_URL="${_emb}"
  fi
fi
export EMBEDDING_SERVICE_URL="${EMBEDDING_SERVICE_URL:-http://localhost:8001}"

# Live scraper (VECINITA_SCRAPER_API_URL + SCRAPER_API_KEYS) for ACTIVE_CRAWL_USE_LIVE_SCRAPER / --live-scraper
if [[ -z "${VECINITA_SCRAPER_API_URL:-}" && -f "${REPO_ROOT}/.env" ]]; then
  _vsu="$(grep -E '^VECINITA_SCRAPER_API_URL=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ -n "${_vsu:-}" ]]; then
    export VECINITA_SCRAPER_API_URL="${_vsu}"
  fi
fi
if [[ -z "${SCRAPER_API_KEYS:-}" && -f "${REPO_ROOT}/.env" ]]; then
  _keys="$(grep -E '^SCRAPER_API_KEYS=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ -n "${_keys:-}" ]]; then
    export SCRAPER_API_KEYS="${_keys}"
  fi
fi
if [[ -z "${ACTIVE_CRAWL_USE_LIVE_SCRAPER:-}" && -f "${REPO_ROOT}/.env" ]]; then
  _ac_live="$(grep -E '^ACTIVE_CRAWL_USE_LIVE_SCRAPER=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ -n "${_ac_live:-}" ]]; then
    export ACTIVE_CRAWL_USE_LIVE_SCRAPER="${_ac_live}"
  fi
fi

cd "${REPO_ROOT}/backend"
exec uv run python -m src.services.scraper.active_crawl "$@"

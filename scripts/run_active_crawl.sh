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

cd "${REPO_ROOT}/backend"
exec uv run python -m src.services.scraper.active_crawl "$@"

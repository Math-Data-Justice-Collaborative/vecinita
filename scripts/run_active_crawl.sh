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

cd "${REPO_ROOT}/backend"
exec uv run python -m src.services.scraper.active_crawl "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

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

export VECINITA_SCRAPER_API_URL="${VECINITA_SCRAPER_API_URL:-https://vecinita-data-management-api-v1-lx27.onrender.com}"

cd "${REPO_ROOT}/backend"
exec uv run python -m src.services.scraper.remote_jobs_runner "$@"

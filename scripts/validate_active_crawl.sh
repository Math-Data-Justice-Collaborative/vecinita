#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -z "${DATABASE_URL:-}" && -f "${REPO_ROOT}/.env" ]]; then
  DATABASE_URL="$(grep -E '^DATABASE_URL=' "${REPO_ROOT}/.env" | head -1 | cut -d= -f2- | tr -d '\r')"
  export DATABASE_URL
fi
if [[ -n "${DATABASE_URL:-}" ]]; then
  DATABASE_URL="${DATABASE_URL//$'\r'/}"
  export DATABASE_URL
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[active-crawl-validate] DATABASE_URL is not set; skipping." >&2
  exit 0
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "[active-crawl-validate] psql is not installed; skipping." >&2
  exit 0
fi

echo "[active-crawl-validate] Recent crawl_runs and latest run attempts"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "${REPO_ROOT}/scripts/validate_active_crawl.sql"

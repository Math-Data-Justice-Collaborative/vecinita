#!/usr/bin/env bash
set -euo pipefail

# Run scraper pipeline, then run Postgres validation queries.
# Defaults to local additive streaming mode.

MODE="local"
RUN_SCRAPER=1
RUN_VALIDATE=1
VERBOSE=0
DEBUG=0
CLEAN=0
NO_CONFIRM=0
NO_STREAM=0
SOURCE_FILTER=""
LIMIT=20
WAIT_FOR_DB_SECONDS="${WAIT_FOR_DB_SECONDS:-90}"
WAIT_FOR_DB_INTERVAL_SECONDS="${WAIT_FOR_DB_INTERVAL_SECONDS:-3}"

usage() {
  cat <<'EOF'
Usage: scripts/run_scraper_postgres_batch.sh [options]

Options:
  --local                  Run scraper locally (default)
  --docker                 Run scraper in docker mode
  --skip-scraper           Skip scraper run and only execute validation queries
  --skip-validate          Skip Postgres validation queries
  --clean                  Clean vector records before scraping (destructive)
  --no-confirm             Skip confirmation for clean mode
  --no-stream              Disable streaming uploads during scraper run
  --verbose                Enable verbose scraper logs
  --debug                  Enable scraper debug mode
  --source-filter <text>   Filter validation queries by source_url/domain text
  --limit <n>              Validation row limit (default: 20)
  --wait-for-db-seconds <n>        Max seconds to wait for DATABASE_URL (default: 90)
  --wait-for-db-interval <n>       Seconds between DB probes (default: 3)
  -h, --help               Show this help

Examples:
  scripts/run_scraper_postgres_batch.sh --local --verbose
  scripts/run_scraper_postgres_batch.sh --docker --source-filter ri.gov
  scripts/run_scraper_postgres_batch.sh --skip-scraper --source-filter wrwc.org
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local)
      MODE="local"
      ;;
    --docker)
      MODE="docker"
      ;;
    --skip-scraper)
      RUN_SCRAPER=0
      ;;
    --skip-validate)
      RUN_VALIDATE=0
      ;;
    --clean)
      CLEAN=1
      ;;
    --no-confirm)
      NO_CONFIRM=1
      ;;
    --no-stream)
      NO_STREAM=1
      ;;
    --verbose)
      VERBOSE=1
      ;;
    --debug)
      DEBUG=1
      ;;
    --source-filter)
      SOURCE_FILTER="${2:-}"
      shift
      ;;
    --limit)
      LIMIT="${2:-20}"
      shift
      ;;
    --wait-for-db-seconds)
      WAIT_FOR_DB_SECONDS="${2:-90}"
      shift
      ;;
    --wait-for-db-interval)
      WAIT_FOR_DB_INTERVAL_SECONDS="${2:-3}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

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

wait_for_postgres() {
  local timeout="$1"
  local interval="$2"
  local waited=0

  if [[ -z "${DATABASE_URL:-}" ]]; then
    return 0
  fi

  if ! command -v psql >/dev/null 2>&1; then
    echo "[scraper-batch] psql not installed; skipping DATABASE_URL readiness wait."
    return 0
  fi

  while (( waited < timeout )); do
    if PGCONNECT_TIMEOUT=5 psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT 1;" >/dev/null 2>&1; then
      echo "[scraper-batch] DATABASE_URL is reachable."
      return 0
    fi
    sleep "$interval"
    waited=$((waited + interval))
  done

  echo "[scraper-batch] DATABASE_URL did not become reachable within ${timeout}s." >&2
  return 1
}

if [[ "$RUN_SCRAPER" -eq 1 ]]; then
  wait_for_postgres "$WAIT_FOR_DB_SECONDS" "$WAIT_FOR_DB_INTERVAL_SECONDS"

  SCRAPER_ARGS=("--${MODE}")

  if [[ "$CLEAN" -eq 1 ]]; then
    SCRAPER_ARGS+=("--clean")
  fi
  if [[ "$NO_CONFIRM" -eq 1 ]]; then
    SCRAPER_ARGS+=("--no-confirm")
  fi
  if [[ "$NO_STREAM" -eq 1 ]]; then
    SCRAPER_ARGS+=("--no-stream")
  fi
  if [[ "$VERBOSE" -eq 1 ]]; then
    SCRAPER_ARGS+=("--verbose")
  fi
  if [[ "$DEBUG" -eq 1 ]]; then
    SCRAPER_ARGS+=("--debug")
  fi

  echo "[scraper-batch] Running scraper pipeline: backend/scripts/run_scraper.sh ${SCRAPER_ARGS[*]}"
  (cd "$REPO_ROOT" && backend/scripts/run_scraper.sh "${SCRAPER_ARGS[@]}")
fi

if [[ "$RUN_VALIDATE" -eq 0 ]]; then
  echo "[scraper-batch] Validation skipped by flag"
  exit 0
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[scraper-batch] DATABASE_URL is not set. Skipping Postgres validation queries."
  exit 0
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "[scraper-batch] psql is not installed. Skipping Postgres validation queries."
  exit 0
fi

wait_for_postgres "$WAIT_FOR_DB_SECONDS" "$WAIT_FOR_DB_INTERVAL_SECONDS"

FILTER_SQL="TRUE"
if [[ -n "$SOURCE_FILTER" ]]; then
  # Minimal SQL escaping for single quotes in ad-hoc filter value.
  SAFE_FILTER="${SOURCE_FILTER//\'/''}"
  FILTER_SQL="(source_url ILIKE '%${SAFE_FILTER}%' OR source_domain ILIKE '%${SAFE_FILTER}%')"
fi

echo "[scraper-batch] Running Postgres validation queries"

echo "[scraper-batch] Query 1: total chunks and unique sources"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "
SELECT
  COUNT(*)::bigint AS total_chunks,
  COUNT(DISTINCT COALESCE(NULLIF(source_url, ''), source_domain))::bigint AS unique_sources
FROM public.document_chunks
WHERE ${FILTER_SQL};
"

echo "[scraper-batch] Query 2: top domains by chunk count"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "
SELECT
  COALESCE(NULLIF(source_domain, ''), 'unknown') AS source_domain,
  COUNT(*)::bigint AS chunk_count,
  COUNT(*) FILTER (WHERE embedding IS NOT NULL)::bigint AS chunks_with_embedding,
  MAX(COALESCE(updated_at, created_at)) AS last_updated
FROM public.document_chunks
WHERE ${FILTER_SQL}
GROUP BY 1
ORDER BY 2 DESC
LIMIT ${LIMIT};
"

echo "[scraper-batch] Query 3: latest ingested records"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "
SELECT
  source_url,
  chunk_index,
  char_length(COALESCE(content, '')) AS content_len,
  (embedding IS NOT NULL) AS has_embedding,
  COALESCE(updated_at, created_at) AS touched_at
FROM public.document_chunks
WHERE ${FILTER_SQL}
ORDER BY COALESCE(updated_at, created_at) DESC
LIMIT ${LIMIT};
"

echo "[scraper-batch] Completed"

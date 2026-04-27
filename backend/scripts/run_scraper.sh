#!/usr/bin/env bash
set -euo pipefail

# Canonical scraper runner for local and Docker workflows.
# Defaults to streaming mode so chunks are uploaded during scraping.

MODE="local"
USE_STREAM=1
CLEAN=0
NO_CONFIRM=0
VERBOSE=0
DEBUG=0

usage() {
  cat <<'EOF'
Usage: backend/scripts/run_scraper.sh [options]

Options:
  --local           Run locally with uv (default)
  --docker          Run inside Docker service vecinita-agent
  --clean           Truncate database before scraping
  --no-confirm      Skip clean confirmation prompt
  --no-stream       Disable streaming upload mode
  --debug           Enable debug mode (writes local chunk files)
  --verbose         Enable verbose logs
  -h, --help        Show this help

Examples:
  backend/scripts/run_scraper.sh --local --verbose
  backend/scripts/run_scraper.sh --docker --clean --no-confirm
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
    --clean)
      CLEAN=1
      ;;
    --no-confirm)
      NO_CONFIRM=1
      ;;
    --no-stream)
      USE_STREAM=0
      ;;
    --debug)
      DEBUG=1
      ;;
    --verbose)
      VERBOSE=1
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
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

WAIT_FOR_SERVICES="${WAIT_FOR_SERVICES:-1}"
SERVICE_WAIT_TIMEOUT_SECONDS="${SERVICE_WAIT_TIMEOUT_SECONDS:-90}"
SERVICE_WAIT_INTERVAL_SECONDS="${SERVICE_WAIT_INTERVAL_SECONDS:-2}"

CLI_ARGS=()
if [[ "$CLEAN" -eq 1 ]]; then
  echo "⚠️  --clean truncates vector records in PostgreSQL and should be used only for intentional resets."
  CLI_ARGS+=("--clean")
fi
if [[ "$NO_CONFIRM" -eq 1 ]]; then
  CLI_ARGS+=("--no-confirm")
fi
if [[ "$USE_STREAM" -eq 1 ]]; then
  CLI_ARGS+=("--stream")
fi
if [[ "$DEBUG" -eq 1 ]]; then
  CLI_ARGS+=("--debug")
fi
if [[ "$VERBOSE" -eq 1 ]]; then
  CLI_ARGS+=("--verbose")
fi

if [[ "$MODE" == "local" ]]; then
  cd "$REPO_ROOT/backend"

  if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required for local mode. Install: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi

  if [[ ! -e data && -d "$REPO_ROOT/data" ]]; then
    ln -s ../data data
  fi

  if [[ -f "$ENV_FILE" ]]; then
    if [[ -z "${EMBEDDING_UPSTREAM_URL:-}" ]]; then
      _emb="$(grep -E '^EMBEDDING_UPSTREAM_URL=' "$ENV_FILE" | sed -n '1p' | cut -d= -f2- | tr -d '\r' || true)"
      if [[ -n "${_emb:-}" ]]; then
        export EMBEDDING_UPSTREAM_URL="${_emb}"
      fi
    fi
    if [[ -z "${EMBEDDING_UPSTREAM_URL:-}" ]]; then
      _legacy="$(grep -E '^EMBEDDING_SERVICE_URL=' "$ENV_FILE" | sed -n '1p' | cut -d= -f2- | tr -d '\r' || true)"
      if [[ -n "${_legacy:-}" ]]; then
        export EMBEDDING_UPSTREAM_URL="${_legacy}"
      fi
    fi
    if [[ -z "${DATA_MANAGEMENT_API_URL:-}" ]]; then
      _dm="$(grep -E '^DATA_MANAGEMENT_API_URL=' "$ENV_FILE" | sed -n '1p' | cut -d= -f2- | tr -d '\r' || true)"
      if [[ -n "${_dm:-}" ]]; then
        export DATA_MANAGEMENT_API_URL="${_dm}"
      fi
    fi
  fi

  export EMBEDDING_UPSTREAM_URL="${EMBEDDING_UPSTREAM_URL:-http://localhost:8001}"
  export DATA_MANAGEMENT_API_URL="${DATA_MANAGEMENT_API_URL:-http://localhost:8005}"

  wait_for_http() {
    local label="$1"
    local url="$2"
    local timeout="$3"
    local interval="$4"
    local waited=0

    if ! command -v curl >/dev/null 2>&1; then
      echo "curl not installed; skipping $label readiness check"
      return 0
    fi

    while (( waited < timeout )); do
      if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
        echo "$label is ready at $url"
        return 0
      fi
      sleep "$interval"
      waited=$((waited + interval))
    done

    echo "$label did not become ready within ${timeout}s at $url" >&2
    return 1
  }

  wait_for_embedding_service() {
    local timeout="$1"
    local interval="$2"
    local health_url="${EMBEDDING_UPSTREAM_URL%/}/health"
    local base_url="${EMBEDDING_UPSTREAM_URL%/}/"

    if wait_for_http "Embedding service" "$health_url" "$timeout" "$interval"; then
      return 0
    fi

    wait_for_http "Embedding service (root fallback)" "$base_url" "$timeout" "$interval"
  }

  if [[ "$WAIT_FOR_SERVICES" == "1" || "$WAIT_FOR_SERVICES" == "true" ]]; then
    wait_for_embedding_service \
      "$SERVICE_WAIT_TIMEOUT_SECONDS" \
      "$SERVICE_WAIT_INTERVAL_SECONDS"
    if [[ -n "${DATA_MANAGEMENT_API_URL:-}" ]]; then
      wait_for_http \
        "Data-management API" \
        "${DATA_MANAGEMENT_API_URL%/}/health" \
        "$SERVICE_WAIT_TIMEOUT_SECONDS" \
        "$SERVICE_WAIT_INTERVAL_SECONDS" || true
    fi
  fi

  echo "Running scraper locally with args: ${CLI_ARGS[*]:-(default)}"
  uv run -m src.services.scraper.cli "${CLI_ARGS[@]}"
  exit 0
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is required for --docker mode." >&2
  exit 1
fi

cd "$REPO_ROOT"
echo "Running scraper in Docker (service: vecinita-agent) with args: ${CLI_ARGS[*]:-(default)}"
"${COMPOSE[@]}" exec -T vecinita-agent uv run -m src.services.scraper.cli "${CLI_ARGS[@]}"

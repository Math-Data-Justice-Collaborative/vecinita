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

CLI_ARGS=()
if [[ "$CLEAN" -eq 1 ]]; then
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

  export EMBEDDING_SERVICE_URL="${EMBEDDING_SERVICE_URL:-http://localhost:8001}"
  echo "Running scraper locally with args: ${CLI_ARGS[*]:-(default)}"
  uv run -m src.scraper.cli "${CLI_ARGS[@]}"
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
"${COMPOSE[@]}" exec -T vecinita-agent uv run -m src.scraper.cli "${CLI_ARGS[@]}"

#!/bin/bash
set -euo pipefail

# ==============================================================================
# SCRIPT: stop_dev_public.sh
# DESCRIPTION: Stop and remove Vecinita dev stack resources created by
#              docker-compose.dev.yml. Removes orphans by default.
# USAGE:
#   ./run/stop_dev_public.sh
#   ./run/stop_dev_public.sh --volumes
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$BASE_DIR/docker-compose.dev.yml"
REMOVE_VOLUMES=false

usage() {
  cat <<EOF
Usage:
  $0 [--volumes]

Options:
  --volumes   Also remove named volumes for the dev stack
  -h, --help  Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --volumes)
      REMOVE_VOLUMES=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "❌ Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "❌ Compose file not found: $COMPOSE_FILE"
  exit 1
fi

echo "🛑 Stopping dev stack from: $COMPOSE_FILE"

if [[ "$REMOVE_VOLUMES" == true ]]; then
  echo "⚠️  --volumes will permanently delete local Postgres persisted data for this dev stack."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans --volumes
else
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
fi

echo "✅ Dev stack stopped"

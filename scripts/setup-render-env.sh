#!/usr/bin/env bash
# Push Modal / embedding runtime env vars to a Render web service from local dotenv files.
#
# Prerequisites:
#   - render login   (when using --service-name; omit if you pass --service-id)
#   - RENDER_API_KEY in the environment or in a merged --file (e.g. .env)
#
# Usage:
#   ./scripts/setup-render-env.sh --dry-run
#   ./scripts/setup-render-env.sh --yes
#   RENDER_SERVICE_NAME=vecinita-agent ./scripts/setup-render-env.sh --yes
#   ./scripts/setup-render-env.sh --file .env --file .env.local --service-name vecinita-gateway --yes
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVICE_NAME="${RENDER_SERVICE_NAME:-vecinita-gateway}"
SERVICE_ID="${RENDER_SERVICE_ID:-}"
DOTENV_PATHS=()
DO_YES=0

usage() {
  cat <<EOF
Usage: $0 [--file PATH]... [--service-name NAME] [--service-id srv-...] [--dry-run|--yes]

Defaults: --file .env --service-name ${SERVICE_NAME}
  (override with RENDER_SERVICE_NAME / RENDER_SERVICE_ID)

Runs: python3 scripts/env_sync.py render-api --preset render-runtime-modal
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    --file)
      DOTENV_PATHS+=("${2:?--file requires a path}")
      shift 2
      ;;
    --service-name)
      SERVICE_NAME="${2:?--service-name requires a value}"
      shift 2
      ;;
    --service-id)
      SERVICE_ID="${2:?--service-id requires a value}"
      shift 2
      ;;
    --dry-run)
      DO_YES=0
      shift
      ;;
    --yes)
      DO_YES=1
      shift
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${#DOTENV_PATHS[@]} -eq 0 ]]; then
  DOTENV_PATHS=(".env")
fi

if ! command -v python3 &>/dev/null; then
  echo "error: python3 required" >&2
  exit 1
fi

FILE_ARGS=()
for p in "${DOTENV_PATHS[@]}"; do
  FILE_ARGS+=(--file "$p")
done

svc_args=(--service-name "$SERVICE_NAME")
if [[ -n "$SERVICE_ID" ]]; then
  svc_args=(--service-id "$SERVICE_ID")
fi

flags=(--dry-run)
if [[ "$DO_YES" -eq 1 ]]; then
  flags=(--yes)
fi

exec python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  "${FILE_ARGS[@]}" \
  "${svc_args[@]}" \
  "${flags[@]}"

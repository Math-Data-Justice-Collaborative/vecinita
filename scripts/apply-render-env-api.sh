#!/usr/bin/env bash
# Non-interactive: PATCH Render service env from dotenv (REST). Same preset as setup-render-env.sh.
#
# RENDER_API_KEY may be in the environment or inside the merged --file (e.g. .env).
#
# Usage:
#   ./scripts/apply-render-env-api.sh --yes
#   ./scripts/apply-render-env-api.sh --file .env.prod.render --service-id srv-xxxxx --yes
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
Usage: $0 [--file PATH]... [--service-name NAME] [--service-id srv-...] --yes

Requires --yes. Reads RENDER_API_KEY from env or from dotenv files.

Defaults: --file .env --service-name ${SERVICE_NAME}
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

if [[ "$DO_YES" -ne 1 ]]; then
  echo "error: refusing to PATCH Render without explicit --yes" >&2
  usage >&2
  exit 1
fi

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

exec python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  "${FILE_ARGS[@]}" \
  "${svc_args[@]}" \
  --yes

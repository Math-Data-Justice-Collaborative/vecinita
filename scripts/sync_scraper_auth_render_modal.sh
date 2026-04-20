#!/usr/bin/env bash
# Sync scraper Bearer auth to Render (REST) and Modal (Secret), using Render CLI for
# service discovery and Modal CLI for vecinita-scraper-env.
#
# Prerequisites
#   Render:
#     - render login
#     - RENDER_API_KEY in the shell or in the merged dotenv (Dashboard → Account → API keys)
#   Modal:
#     - modal token set ...  (or modal setup)
#
# Usage
#   ./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --dry-run
#   ./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes
#   RENDER_SERVICE_ID=srv-... ./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes
#
#   ./scripts/sync_scraper_auth_render_modal.sh modal --from-dotenv ~/secrets/vecinita-scraper-modal.env --force
#
# Notes
#   - render-api uses PATCH (see scripts/env_sync.py); only keys present in the dotenv file
#     and selected by --key are sent.
#   - Modal: --force replaces the entire secret. Use a dotenv that contains every key the
#     scraper Modal image needs (MODAL_DATABASE_URL with Render *external* Postgres URL,
#     MODAL_SCRAPER_PERSIST_VIA_GATEWAY matching the gateway, SCRAPER_API_KEYS, upstream URLs,
#     CORS, …). Internal dpg-*-a DATABASE_URL from Render blueprints will not resolve from Modal
#     — see docs/deployment/RENDER_SHARED_ENV_CONTRACT.md.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVICE_NAME="${RENDER_SCRAPER_SERVICE_NAME:-vecinita-data-management-api-v1}"
MODAL_SECRET_NAME="${MODAL_SCRAPER_SECRET_NAME:-vecinita-scraper-env}"

die() {
  echo "error: $*" >&2
  exit 1
}

render_resolve_service_id() {
  local name="$1"
  if ! render services -o json 2>/dev/null | python3 -c "
import json
import sys

name = sys.argv[1]
raw = sys.stdin.read()
if not raw.strip():
    raise SystemExit('empty JSON from render services')
data = json.loads(raw)
if isinstance(data, dict):
    if isinstance(data.get('items'), list):
        data = data['items']
    elif isinstance(data.get('services'), list):
        data = data['services']
    else:
        data = [data]
if not isinstance(data, list):
    raise SystemExit('unexpected JSON shape from render services')

for item in data:
    if not isinstance(item, dict):
        continue
    if item.get('serviceType') == 'datastore':
        continue
    if item.get('name') == name:
        sid = item.get('id') or item.get('serviceId')
        if sid:
            print(sid)
            raise SystemExit(0)
raise SystemExit(1)
" "$name"; then
    die "could not resolve Render service id for name '$name' — run: render login; or set RENDER_SERVICE_ID"
  fi
}

usage() {
  cat <<EOF
Usage:
  $0 render --dotenv PATH [--dry-run|--yes] [--service-name NAME]
  $0 modal --from-dotenv PATH [--force]   # --force required to overwrite existing secret

Environment:
  RENDER_API_KEY          required for render (unless --dry-run)
  RENDER_SERVICE_ID       optional; skips Render CLI lookup if set
  RENDER_SCRAPER_SERVICE_NAME  default: ${SERVICE_NAME}
  MODAL_SCRAPER_SECRET_NAME    default: ${MODAL_SECRET_NAME}
EOF
}

cmd_render() {
  local dotenv="" dry=1 yes=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dotenv)
        dotenv="${2:-}"
        shift 2
        ;;
      --dry-run)
        dry=1
        shift
        ;;
      --yes)
        yes=1
        dry=0
        shift
        ;;
      --service-name)
        SERVICE_NAME="${2:-}"
        shift 2
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        die "unknown flag: $1"
        ;;
    esac
  done
  [[ -n "$dotenv" ]] || die "render mode requires --dotenv PATH"
  [[ -f "$dotenv" ]] || die "dotenv file not found: $dotenv"

  local sid="${RENDER_SERVICE_ID:-}"
  if [[ -z "$sid" ]]; then
    sid="$(render_resolve_service_id "$SERVICE_NAME")" || die "could not resolve Render service id for name '$SERVICE_NAME'"
  fi
  echo "Using Render service id: $sid (name: $SERVICE_NAME)"

  local extra=(--key SCRAPER_API_KEYS)
  # Optional compatibility key if present in file
  if grep -q '^[[:space:]]*DEV_ADMIN_BEARER_TOKEN=' "$dotenv" 2>/dev/null; then
    extra+=(--key DEV_ADMIN_BEARER_TOKEN)
  fi

  if [[ "$dry" -eq 1 ]]; then
    RENDER_API_KEY="${RENDER_API_KEY:-}" python3 scripts/env_sync.py render-api \
      --file "$dotenv" \
      --service-id "$sid" \
      "${extra[@]}" \
      --dry-run
    echo "Dry-run only. Re-run with --yes to PATCH Render (requires RENDER_API_KEY)."
    return 0
  fi

  # RENDER_API_KEY may be set in the shell or only inside the dotenv file (env_sync merges --file first).
  python3 scripts/env_sync.py render-api \
    --file "$dotenv" \
    --service-id "$sid" \
    "${extra[@]}" \
    --yes
  echo "Render updated. Trigger a deploy or wait for auto-redeploy if configured."
}

cmd_modal() {
  local from="" force=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from-dotenv)
        from="${2:-}"
        shift 2
        ;;
      --force)
        force=(--force)
        shift
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        die "unknown flag: $1"
        ;;
    esac
  done
  [[ -n "$from" ]] || die "modal mode requires --from-dotenv PATH"
  [[ -f "$from" ]] || die "dotenv file not found: $from"

  modal secret create "$MODAL_SECRET_NAME" "${force[@]}" --from-dotenv "$from"
  echo "Modal secret '${MODAL_SECRET_NAME}' updated from $from"
}

main() {
  [[ $# -ge 1 ]] || {
    usage
    exit 1
  }
  case "$1" in
    render)
      shift
      cmd_render "$@"
      ;;
    modal)
      shift
      cmd_modal "$@"
      ;;
    -h | --help)
      usage
      ;;
    *)
      die "first argument must be 'render' or 'modal'"
      ;;
  esac
}

main "$@"

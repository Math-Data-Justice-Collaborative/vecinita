#!/usr/bin/env bash
set -euo pipefail

# Run one gateway deploy troubleshooting iteration for a target environment.
# Sequence: validate runtime -> trigger deploy -> wait for live -> smoke checks.

ENVIRONMENT="${1:-staging}"

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo "Usage: $0 [staging|production]"
  exit 1
fi

if [[ -z "${RENDER_API_KEY:-}" ]]; then
  echo "RENDER_API_KEY is required"
  exit 1
fi

if [[ "$ENVIRONMENT" == "staging" ]]; then
  SERVICE_NAME="vecinita-gateway-staging"
  SERVICE_ID="${RENDER_STAGING_GATEWAY_SERVICE_ID:-}"
  DEPLOY_HOOK="${RENDER_STAGING_DEPLOY_HOOK_GATEWAY:-}"
  PUBLIC_URL="${RENDER_STAGING_GATEWAY_URL:-}"
else
  SERVICE_NAME="vecinita-gateway"
  SERVICE_ID="${RENDER_GATEWAY_SERVICE_ID:-}"
  DEPLOY_HOOK="${RENDER_PROD_DEPLOY_HOOK_GATEWAY:-${RENDER_DEPLOY_HOOK_GATEWAY:-}}"
  PUBLIC_URL="${RENDER_PROD_GATEWAY_URL:-${RENDER_GATEWAY_URL:-}}"
fi

if [[ -z "$SERVICE_ID" ]]; then
  echo "Missing service id for $ENVIRONMENT"
  exit 1
fi

echo "[iteration] validating runtime for $SERVICE_NAME"
python3 scripts/github/validate_render_runtime.py \
  --service-id "$SERVICE_ID" \
  --service-name "$SERVICE_NAME" \
  --expect docker

if [[ -n "$DEPLOY_HOOK" ]]; then
  echo "[iteration] triggering deploy via hook"
  curl -fsSL -X POST "$DEPLOY_HOOK" >/dev/null
else
  echo "[iteration] triggering deploy via Render API"
  curl -fsSL -X POST "https://api.render.com/v1/services/$SERVICE_ID/deploys" \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{}' >/dev/null
fi

echo "[iteration] waiting for deploy to reach live"
python3 scripts/github/wait_for_render_deploy.py "$SERVICE_ID" --timeout 1200 --interval 30

if [[ -n "$PUBLIC_URL" ]]; then
  echo "[iteration] running smoke checks against $PUBLIC_URL"
  health_status="$(curl -o /dev/null -s -w '%{http_code}' --retry 4 --retry-delay 10 --retry-all-errors "$PUBLIC_URL/health")"
  docs_status="$(curl -o /dev/null -s -w '%{http_code}' --retry 4 --retry-delay 10 --retry-all-errors "$PUBLIC_URL/api/v1/documents/tags?limit=5")"

  echo "[iteration] health status=$health_status"
  echo "[iteration] docs status=$docs_status"

  if [[ "$health_status" -lt 200 || "$health_status" -ge 400 ]]; then
    echo "[iteration] health check failed"
    exit 1
  fi
  if [[ "$docs_status" -lt 200 || "$docs_status" -ge 400 ]]; then
    echo "[iteration] docs endpoint check failed"
    exit 1
  fi
else
  echo "[iteration] no gateway public URL configured; skipping smoke checks"
fi

echo "[iteration] completed successfully for $SERVICE_NAME"

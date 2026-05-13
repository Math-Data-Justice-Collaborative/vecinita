#!/bin/bash
set -euo pipefail

# ==============================================================================
# SCRIPT: start_dev_public.sh
# DESCRIPTION: Configure GCE firewall/tag (optional), then start Vecinita dev stack
#              on docker-compose.dev.yml with public-friendly frontend API URLs.
# USAGE:
#   ./run/start_dev_public.sh --external-ip <EXTERNAL_IP>
#
# Optional GCloud setup (requires authenticated gcloud + permissions):
#   ./run/start_dev_public.sh \
#     --external-ip <EXTERNAL_IP> \
#     --project <GCP_PROJECT_ID> \
#     --zone <GCE_ZONE> \
#     --instance <GCE_INSTANCE_NAME>
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$BASE_DIR/docker-compose.dev.yml"
FIREWALL_RULE_NAME="vecinita-dev-ports"
NETWORK_TAG="vecinita-dev"

EXTERNAL_IP=""
PROJECT_ID=""
ZONE=""
INSTANCE=""

usage() {
  cat <<EOF
Usage:
  $0 --external-ip <EXTERNAL_IP> [--project <GCP_PROJECT_ID> --zone <GCE_ZONE> --instance <GCE_INSTANCE_NAME>]

Required:
  --external-ip   External/public IP (or DNS) for browser clients to reach gateway/frontend

Optional (enables automatic firewall + VM tag setup):
  --project       GCP project ID
  --zone          GCE instance zone
  --instance      GCE instance name

Examples:
  $0 --external-ip 34.123.45.67
  $0 --external-ip 34.123.45.67 --project my-proj --zone us-central1-a --instance vecinita-dev-vm
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --external-ip)
      EXTERNAL_IP="${2:-}"
      shift 2
      ;;
    --project)
      PROJECT_ID="${2:-}"
      shift 2
      ;;
    --zone)
      ZONE="${2:-}"
      shift 2
      ;;
    --instance)
      INSTANCE="${2:-}"
      shift 2
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

if [[ -z "$EXTERNAL_IP" ]]; then
  echo "❌ --external-ip is required"
  usage
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "❌ Compose file not found: $COMPOSE_FILE"
  exit 1
fi

if [[ -n "$PROJECT_ID" || -n "$ZONE" || -n "$INSTANCE" ]]; then
  if [[ -z "$PROJECT_ID" || -z "$ZONE" || -z "$INSTANCE" ]]; then
    echo "❌ If using GCloud automation, provide --project, --zone, and --instance together."
    exit 1
  fi

  echo "🔐 Configuring GCE network tag on instance: $INSTANCE"
  EXISTING_TAGS="$(gcloud compute instances describe "$INSTANCE" \
    --project "$PROJECT_ID" \
    --zone "$ZONE" \
    --format='value(tags.items)' || true)"

  if [[ "$EXISTING_TAGS" == *"$NETWORK_TAG"* ]]; then
    echo "✅ Instance already has tag: $NETWORK_TAG"
  else
    gcloud compute instances add-tags "$INSTANCE" \
      --project "$PROJECT_ID" \
      --zone "$ZONE" \
      --tags "$NETWORK_TAG"
    echo "✅ Added tag: $NETWORK_TAG"
  fi

  echo "🌐 Ensuring firewall rule exists: $FIREWALL_RULE_NAME"
  if gcloud compute firewall-rules describe "$FIREWALL_RULE_NAME" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud compute firewall-rules update "$FIREWALL_RULE_NAME" \
      --project "$PROJECT_ID" \
      --allow tcp:15173,tcp:18004 \
      --target-tags "$NETWORK_TAG" \
      --description "Vecinita dev public ports (frontend/api)"
    echo "✅ Updated firewall rule: $FIREWALL_RULE_NAME"
  else
    gcloud compute firewall-rules create "$FIREWALL_RULE_NAME" \
      --project "$PROJECT_ID" \
      --allow tcp:15173,tcp:18004 \
      --target-tags "$NETWORK_TAG" \
      --description "Vecinita dev public ports (frontend/api)"
    echo "✅ Created firewall rule: $FIREWALL_RULE_NAME"
  fi
else
  echo "ℹ️ Skipping GCloud automation (no --project/--zone/--instance provided)."
fi

echo "🐳 Starting dev stack from: $COMPOSE_FILE"
export VITE_GATEWAY_URL="http://${EXTERNAL_IP}:18004/api/v1"
export VITE_BACKEND_URL="http://${EXTERNAL_IP}:18000"
export ALLOWED_ORIGINS="http://${EXTERNAL_IP}:15173,http://localhost:15173,http://127.0.0.1:15173,http://localhost:5173,http://localhost:5174,http://localhost:4173"

docker compose -f "$COMPOSE_FILE" up -d --build

echo "✅ Dev stack started"
echo "Frontend: http://${EXTERNAL_IP}:15173"
echo "API:      http://${EXTERNAL_IP}:18004/api/v1"

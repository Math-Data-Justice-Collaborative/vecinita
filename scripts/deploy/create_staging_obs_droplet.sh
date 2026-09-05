#!/usr/bin/env bash
# Create staging observability Droplet (F84 / ADR-055 / EV-036-D13).
# Requires doctl with Droplet read+write scopes. Staging only — ~$6/mo s-1vcpu-1gb.
set -euo pipefail

NAME="${VECINITA_OBS_DROPLET_NAME:-vecinita-staging-obs}"
SIZE="${VECINITA_OBS_DROPLET_SIZE:-s-1vcpu-1gb}"
REGION="${VECINITA_OBS_DROPLET_REGION:-nyc3}"
IMAGE="${VECINITA_OBS_DROPLET_IMAGE:-docker-20-04}"
SSH_KEY_IDS="${VECINITA_OBS_SSH_KEY_IDS:-}"

echo "Checking doctl Droplet authorization…"
if [[ -z "${DIGITALOCEAN_ACCESS_TOKEN:-}" && -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
  if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    set -a && source .env && set +a
  elif [[ -f ../../.env ]]; then
    # shellcheck disable=SC1091
    set -a && source ../../.env && set +a
  fi
fi
if [[ -n "${DIGITALOCEAN_TOKEN:-}" && -z "${DIGITALOCEAN_ACCESS_TOKEN:-}" ]]; then
  export DIGITALOCEAN_ACCESS_TOKEN="$DIGITALOCEAN_TOKEN"
fi
if ! doctl compute droplet list >/dev/null 2>&1; then
  cat <<'EOF'
ERROR: doctl cannot list Droplets (403 or auth failure).

Set DIGITALOCEAN_TOKEN in repo-root .env (gitignored), or:

  export DIGITALOCEAN_ACCESS_TOKEN=…
  # or: doctl auth init

Token must include Droplet read+write. Re-run this script after auth succeeds.
EOF
  exit 1
fi

if doctl compute droplet list --format Name --no-header | grep -qx "$NAME"; then
  echo "Droplet already exists: $NAME"
  doctl compute droplet get "$NAME" --format ID,Name,PublicIPv4,Status,Region,Memory,VCPUs
  exit 0
fi

ARGS=(
  compute droplet create "$NAME"
  --size "$SIZE"
  --image "$IMAGE"
  --region "$REGION"
  --wait
  --tag-name "vecinita"
  --tag-name "staging"
  --tag-name "observability"
  --enable-monitoring
)

if [[ -n "$SSH_KEY_IDS" ]]; then
  ARGS+=(--ssh-keys "$SSH_KEY_IDS")
else
  # Prefer first account SSH key if present
  FIRST_KEY="$(doctl compute ssh-key list --format ID --no-header 2>/dev/null | head -1 || true)"
  if [[ -n "$FIRST_KEY" ]]; then
    ARGS+=(--ssh-keys "$FIRST_KEY")
  else
    echo "WARNING: no SSH keys on the DO account; droplet will use password/email reset."
  fi
fi

echo "Creating Droplet: name=$NAME size=$SIZE region=$REGION image=$IMAGE"
doctl "${ARGS[@]}"

echo
echo "Next:"
echo "  1. SSH in and clone/copy infra/observability/"
echo "  2. cp .env.example .env  # set GRAFANA_ADMIN_PASSWORD + webhook"
echo "  3. Render alertmanager webhook URL (see infra/observability/README.md)"
echo "  4. docker compose up -d"
echo "  5. Complete infra/observability/CHECKLIST-tc305-tc306.md"
echo
doctl compute droplet get "$NAME" --format ID,Name,PublicIPv4,Status,Region,Memory,VCPUs

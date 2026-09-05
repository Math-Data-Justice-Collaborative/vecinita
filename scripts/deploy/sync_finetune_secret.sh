#!/usr/bin/env bash
# Sync the Modal `vecinita-llm-finetune` secret from the current shell env.
#
# Used by infra/modal/finetune_app.py for LoRA train/eval. Safe defaults keep the
# feature disabled until a later explicit approval gate.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/deploy/sync_finetune_secret.sh            # dry run
#   bash scripts/deploy/sync_finetune_secret.sh --apply    # write secret
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
  esac
done

# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

SECRET_NAME="vecinita-llm-finetune"
REQUIRED_KEYS=(
  VECINITA_INTERNAL_WRITE_URL
  VECINITA_INTERNAL_API_KEY
)
OPTIONAL_KEYS=(
  VECINITA_AUTOMATIONS_KILL_SWITCH
  VECINITA_FINETUNE_ENABLED
  VECINITA_FINETUNE_REQUIRE_APPROVE
  VECINITA_FINETUNE_MAX_CONCURRENT
  VECINITA_FINETUNE_MAX_RUNS_PER_DAY
)

PAIRS=()
MISSING=()
for key in "${REQUIRED_KEYS[@]}"; do
  val="${!key:-}"
  if [[ -z "$val" ]]; then
    MISSING+=("$key")
    continue
  fi
  PAIRS+=("$key=$val")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: missing required env vars for ${SECRET_NAME}:" >&2
  printf '  - %s\n' "${MISSING[@]}" >&2
  echo "Source prod.env (set -a && source prod.env && set +a). See infra/modal/.env.example." >&2
  exit 1
fi

# Safe rollout defaults per ADR-052 / ADR-053: deploy the path first, keep FT off.
: "${VECINITA_AUTOMATIONS_KILL_SWITCH:=false}"
: "${VECINITA_FINETUNE_ENABLED:=false}"
: "${VECINITA_FINETUNE_REQUIRE_APPROVE:=true}"
: "${VECINITA_FINETUNE_MAX_CONCURRENT:=1}"
: "${VECINITA_FINETUNE_MAX_RUNS_PER_DAY:=3}"

for key in "${OPTIONAL_KEYS[@]}"; do
  PAIRS+=("$key=${!key}")
done

echo "==> Modal secret: ${SECRET_NAME}"
echo "    Keys to push (values hidden):"
for pair in "${PAIRS[@]}"; do
  echo "      - ${pair%%=*}"
done

if [[ "$APPLY" -ne 1 ]]; then
  echo "Dry run. Re-run with --apply to write the secret."
  exit 0
fi

modal secret create --force "${SECRET_NAME}" "${PAIRS[@]}"
echo "OK: updated Modal secret ${SECRET_NAME}."
echo "Redeploy finetune app: modal deploy infra/modal/finetune_app.py"

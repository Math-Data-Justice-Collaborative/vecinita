#!/usr/bin/env bash
# Sync Modal LLM secrets from the current shell env (ADR-037 / EV-313).
#
# 1) ``vecinita-llm`` — ASGI proxy auth only (``VECINITA_MODAL_PROXY_KEY``).
#    Used by infra/modal/llm_app.py and llm_playground_app.py ASGI routes.
#    Key must match DO internal-write-api / chat-rag-backend VECINITA_MODAL_PROXY_KEY.
#
# 2) ``vecinita-llm-gpu`` — GPU worker env (no proxy key): promote pin + playground
#    candidate pin + eager A/B. Mounted on prod/playground GPU services.
#
# GPU memory snapshots (``VECINITA_LLM_GPU_SNAPSHOT``) are *not* toggled by these
# secrets: ``enable_memory_snapshot`` is fixed at ``modal deploy`` import time.
# To enable: export the var in the deploy shell, then ``modal deploy infra/modal/llm_app.py``.
#
# Usage:
#   set -a && source .env && set +a
#   bash scripts/deploy/sync_llm_secret.sh            # dry run
#   bash scripts/deploy/sync_llm_secret.sh --apply    # write secrets
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
MERGE=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --merge) MERGE=1 ;;
  esac
done

# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

sync_secret() {
  local secret_name="$1"
  shift
  local -a required_keys=("$@")

  local -a pairs=()
  local -a missing=()
  local key val
  for key in "${required_keys[@]}"; do
    val="${!key:-}"
    if [[ -z "$val" ]]; then
      missing+=("$key")
      continue
    fi
    pairs+=("$key=$val")
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "ERROR: missing required env vars for ${secret_name}:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    echo "Source .env (set -a && source .env && set +a). See infra/modal/.env.example." >&2
    exit 1
  fi

  echo "==> Modal secret: ${secret_name}"
  echo "    Keys to push (values hidden):"
  local pair
  for pair in "${pairs[@]}"; do
    echo "      - ${pair%%=*}"
  done

  if [[ "$APPLY" -ne 1 ]]; then
    echo "    (dry run)"
    return 0
  fi

  modal secret create --force "${secret_name}" "${pairs[@]}"
  echo "OK: updated Modal secret ${secret_name}."
}

sync_optional_secret() {
  local secret_name="$1"
  shift
  local -a optional_keys=("$@")
  local merge_export_ok=0

  if [[ "$MERGE" -eq 1 ]]; then
    echo "==> --merge: reading live ${secret_name} secret to preserve existing keys"
    local export_file="${ROOT}/.tmp/modal-${secret_name}.env"
    mkdir -p "${ROOT}/.tmp"
    if MODAL_SECRET_EXPORT_NAME="$secret_name" \
      uv run --with modal modal run scripts/deploy/export_modal_secret.py >/dev/null 2>&1; then
      merge_export_ok=1
    fi
    if [[ -f "$export_file" ]]; then
      merge_export_ok=1
      while IFS='=' read -r k v; do
        [[ -z "$k" || "$k" == \#* ]] && continue
        if [[ -z "${!k:-}" ]]; then
          export "$k=$v"
        fi
      done < "$export_file"
      echo "    merged live keys from ${export_file#"$ROOT"/}"
    else
      echo "WARN: could not export live secret; proceeding with shell env only." >&2
    fi
  fi

  local -a pairs=()
  local key val
  for key in "${optional_keys[@]}"; do
    val="${!key:-}"
    if [[ -n "$val" ]]; then
      pairs+=("$key=$val")
    fi
  done

  if [[ "$MERGE" -eq 1 && "$merge_export_ok" -ne 1 \
    && -z "${VECINITA_FINETUNE_ADAPTER_ID:-}" \
    && -z "${VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID:-}" ]]; then
    echo "ERROR: Refusing to replace ${secret_name} without live export or explicit adapter pins." >&2
    echo "Set VECINITA_FINETUNE_ADAPTER_ID / VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID, or retry when Modal export works." >&2
    exit 1
  fi

  # Modal secrets need at least one key; default eager flag keeps the store valid.
  if [[ ${#pairs[@]} -eq 0 ]]; then
    pairs+=("VECINITA_LLM_ENFORCE_EAGER=${VECINITA_LLM_ENFORCE_EAGER:-true}")
  fi

  echo "==> Modal secret: ${secret_name}"
  echo "    Keys to push (values hidden):"
  local pair
  for pair in "${pairs[@]}"; do
    echo "      - ${pair%%=*}"
  done

  if [[ "$APPLY" -ne 1 ]]; then
    echo "    (dry run)"
    return 0
  fi

  modal secret create --force "${secret_name}" "${pairs[@]}"
  echo "OK: updated Modal secret ${secret_name}."
}

sync_secret "vecinita-llm" VECINITA_MODAL_PROXY_KEY
sync_optional_secret "vecinita-llm-gpu" \
  VECINITA_FINETUNE_ADAPTER_ID \
  VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID \
  VECINITA_LLM_ENFORCE_EAGER

if [[ "$APPLY" -ne 1 ]]; then
  echo "Dry run. Re-run with --apply to write secrets."
  echo "Use --merge to preserve live adapter pins when shell env omits optional GPU keys."
  echo "Note: VECINITA_LLM_GPU_SNAPSHOT is deploy-time env for modal deploy — not stored here."
  exit 0
fi

echo "Redeploy both LLM apps:"
echo "  modal deploy infra/modal/llm_app.py"
echo "  modal deploy infra/modal/llm_playground_app.py"
echo "Snapshots: export VECINITA_LLM_GPU_SNAPSHOT=true|false in the deploy shell before modal deploy."
echo "Optional: retire deprecated secret vecinita-ollama in Modal dashboard after smoke."

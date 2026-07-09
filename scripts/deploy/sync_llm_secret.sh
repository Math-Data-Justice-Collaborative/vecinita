#!/usr/bin/env bash
# Sync the Modal `vecinita-llm` secret from the current shell env (ADR-037).
#
# Used by infra/modal/llm_app.py ASGI routes for proxy auth on /models/ollama*.
# Key must match DO internal-write-api VECINITA_MODAL_PROXY_KEY.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/deploy/sync_llm_secret.sh            # dry run
#   bash scripts/deploy/sync_llm_secret.sh --apply    # write secret
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

SECRET_NAME="vecinita-llm"
REQUIRED_KEYS=(VECINITA_MODAL_PROXY_KEY)

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
echo "Redeploy LLM app: modal deploy infra/modal/llm_app.py"
echo "Optional: retire deprecated secret vecinita-ollama in Modal dashboard after smoke."

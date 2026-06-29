#!/usr/bin/env bash
# Pre-deploy Modal secrets/volumes/apps check (staging-secrets-matrix + infra/modal).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if ! command -v modal >/dev/null 2>&1; then
  echo "ERROR: modal CLI not found." >&2
  exit 1
fi

# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

REQUIRED_SECRET="vecinita-data-management"
REQUIRED_VOLUMES=(embedding-models llm-models)
REQUIRED_APPS=(vecinita-embedding vecinita-data-management vecinita-llm)

echo "==> Modal profile"
modal profile current

echo "==> Required secret: ${REQUIRED_SECRET}"
secret_names="$(modal secret list --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for row in data:
    print(row.get('Name') or row.get('name', ''))
")"
if ! grep -qx "${REQUIRED_SECRET}" <<<"${secret_names}"; then
  echo "ERROR: missing Modal secret '${REQUIRED_SECRET}'." >&2
  echo "Create with keys (see infra/modal/README.md):" >&2
  echo "  VECINITA_MODAL_EMBED_URL, VECINITA_INTERNAL_WRITE_URL, VECINITA_INTERNAL_API_KEY" >&2
  echo "  VECINITA_MODAL_PROXY_KEY, VECINITA_CORS_ORIGINS, VECINITA_MODAL_LLM_URL" >&2
  echo "  SUPABASE_URL, VECINITA_AUTH_REQUIRED (EV-005 — see infra/modal/.env.example)" >&2
  echo "Existing secrets:" >&2
  echo "${secret_names}" >&2
  exit 1
fi
echo "OK secret ${REQUIRED_SECRET} exists"

echo "==> Required volumes"
vol_names="$(modal volume list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for row in data:
    print(row.get('Name') or row.get('name', ''))
" 2>/dev/null || modal volume list | awk 'NR>2 {print $1}')"
for vol in "${REQUIRED_VOLUMES[@]}"; do
  if ! grep -qx "${vol}" <<<"${vol_names}"; then
    echo "ERROR: missing Modal volume '${vol}' (run scripts/stage_modal_weights.sh)." >&2
    exit 1
  fi
  echo "OK volume ${vol}"
done

echo "==> Deployed apps (advisory)"
app_lines="$(modal app list 2>/dev/null || true)"
for app in "${REQUIRED_APPS[@]}"; do
  if grep -q "${app}" <<<"${app_lines}"; then
    if grep "${app}" <<<"${app_lines}" | grep -qi stopped; then
      echo "WARN: ${app} is stopped — redeploy: bash scripts/deploy/modal.sh" >&2
    else
      echo "OK app ${app} listed"
    fi
  else
    echo "WARN: ${app} not found in modal app list — deploy with scripts/deploy/modal.sh" >&2
  fi
done

echo "==> Advisory: browser connectivity (H4–H5)"
echo "    Set VECINITA_CORS_ORIGINS on DO APIs + Modal data-mgmt; VITE_* on frontends."
echo "    Post-deploy: bash scripts/deploy/verify_connectivity.sh"
echo "    See .cursor/skills/connectivity-gates.md"

echo "OK: verify_secrets passed (DO App Platform secrets are manual — see docs/staging-secrets-matrix.md)."

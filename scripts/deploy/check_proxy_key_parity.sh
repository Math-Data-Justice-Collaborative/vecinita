#!/usr/bin/env bash
# Compare admin frontend build-time proxy key with Modal data-mgmt secret value.
# See docs/staging-secrets-matrix.md and connectivity-gates.md (H5).
set -euo pipefail

vite="${VITE_VECINITA_MODAL_PROXY_KEY:-}"
modal="${VECINITA_MODAL_PROXY_KEY:-}"

if [[ -z "$vite" || -z "$modal" ]]; then
  echo "Usage: export both variables, then run this script." >&2
  echo "  VITE_VECINITA_MODAL_PROXY_KEY — from DO vecinita-admin-frontend BUILD_TIME secret" >&2
  echo "  VECINITA_MODAL_PROXY_KEY       — from Modal secret vecinita-data-management" >&2
  exit 2
fi

if [[ "$vite" == "$modal" ]]; then
  echo "OK: proxy keys match (length ${#vite} chars)."
  exit 0
fi

echo "ERROR: proxy key mismatch — admin bundle will send a different Modal-Key than the API expects (401 on POST /jobs)." >&2
echo "  VITE length: ${#vite}  Modal length: ${#modal}" >&2
echo "Fix: set the same value in both places, redeploy Modal data-mgmt if secret changed, rebuild admin frontend." >&2
exit 1

#!/usr/bin/env bash
# Ensure Modal CLI uses the vecinita workspace (not fontface/cogni-chem).
# Source from deploy/staging scripts: source "$(dirname "$0")/modal_ensure_workspace.sh"
set -euo pipefail

REQUIRED="${VECINITA_MODAL_WORKSPACE:-vecinita}"

if ! command -v modal >/dev/null 2>&1; then
  echo "modal CLI not found. Install: pip install modal" >&2
  exit 1
fi

if ! modal token info >/dev/null 2>&1; then
  echo "Modal CLI is not authenticated. Run: modal token new" >&2
  exit 1
fi

# CI/CD: MODAL_TOKEN_ID + MODAL_TOKEN_SECRET authenticate without a named profile
# in ~/.modal.toml (see https://modal.com/docs/guide/continuous-deployment).
if [[ -n "${MODAL_TOKEN_ID:-}" && -n "${MODAL_TOKEN_SECRET:-}" ]]; then
  WORKSPACE_LINE="$(modal token info 2>/dev/null | sed -n 's/^Workspace: //p' | head -1)"
  CURRENT_WS="${WORKSPACE_LINE%% *}"
  if [[ "$CURRENT_WS" != "$REQUIRED" ]]; then
    echo "Modal token workspace must be '${REQUIRED}' (got '${CURRENT_WS:-unknown}')." >&2
    exit 1
  fi
  echo "==> Modal workspace: ${REQUIRED} (token auth)"
else
  CURRENT="$(modal profile current 2>/dev/null | tr -d '[:space:]')"
  if [[ "$CURRENT" != "$REQUIRED" ]]; then
    echo "==> Switching Modal profile: ${CURRENT:-unknown} -> ${REQUIRED}"
    modal profile activate "$REQUIRED"
  fi

  CURRENT="$(modal profile current 2>/dev/null | tr -d '[:space:]')"
  if [[ "$CURRENT" != "$REQUIRED" ]]; then
    echo "Modal workspace must be '${REQUIRED}' (got '${CURRENT}')." >&2
    echo "Run: modal profile activate ${REQUIRED}" >&2
    exit 1
  fi

  echo "==> Modal workspace: ${REQUIRED}"
fi

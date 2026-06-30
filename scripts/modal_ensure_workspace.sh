#!/usr/bin/env bash
# Ensure Modal CLI uses the vecinita workspace (not fontface/cogni-chem).
# Source from deploy/staging scripts: source "$(dirname "$0")/modal_ensure_workspace.sh"
set -euo pipefail

REQUIRED="${VECINITA_MODAL_WORKSPACE:-vecinita}"

if ! command -v modal >/dev/null 2>&1; then
  echo "modal CLI not found. Install: pip install modal" >&2
  exit 1
fi

_modal_token_info_ok() {
  modal token info >/dev/null 2>&1
}

# CI: Modal API can fail transiently (~60s hang then auth error); retry before aborting.
_wait_for_modal_token() {
  local max_attempts="${MODAL_TOKEN_INFO_RETRIES:-3}"
  local delay="${MODAL_TOKEN_INFO_RETRY_DELAY:-10}"
  local attempt=1
  local last_err=""

  while (( attempt <= max_attempts )); do
    if _modal_token_info_ok; then
      return 0
    fi
    last_err="$(modal token info 2>&1 || true)"
    if (( attempt < max_attempts )); then
      echo "WARN: modal token info attempt ${attempt}/${max_attempts} failed; retry in ${delay}s..." >&2
      sleep "$delay"
    fi
    attempt=$((attempt + 1))
  done

  echo "Modal CLI is not authenticated after ${max_attempts} attempts." >&2
  if [[ -n "$last_err" ]]; then
    echo "Last error: ${last_err}" >&2
  fi
  if [[ -n "${MODAL_TOKEN_ID:-}" && -n "${MODAL_TOKEN_SECRET:-}" ]]; then
    echo "Verify MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in GitHub Actions secrets." >&2
  else
    echo "Run: modal token new" >&2
  fi
  return 1
}

if ! _wait_for_modal_token; then
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

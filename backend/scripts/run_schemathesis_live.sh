#!/usr/bin/env bash
# Live Schemathesis CLI against agent and/or gateway OpenAPI URLs.
#
# Environment:
#   AGENT_SCHEMA_URL     — e.g. https://vecinita-agent-lx27.onrender.com/openapi.json
#   GATEWAY_SCHEMA_URL   — e.g. https://vecinita-gateway-lx27.onrender.com/api/v1/docs/openapi.json
#   SCHEMA_URL           — backward compatible default when only one URL is used
#   GATEWAY_LIVE_BEARER  — optional Bearer token when ENABLE_AUTH=true on gateway
#   SCHEMATHESIS_CHECKS  — default: not_a_server_error
#   SCHEMATHESIS_REPORT_DIR — default: schemathesis-report (under cwd, usually backend/)
#   WAIT_FOR_SCHEMA_SECONDS — default: 30
#   SCHEMATHESIS_MAX_EXAMPLES — maps to --max-examples (default: 12)
set -euo pipefail

WAIT_FOR_SCHEMA_SECONDS="${WAIT_FOR_SCHEMA_SECONDS:-30}"
REPORT_DIR="${SCHEMATHESIS_REPORT_DIR:-schemathesis-report}"
CHECKS="${SCHEMATHESIS_CHECKS:-not_a_server_error}"
MAX_EX="${SCHEMATHESIS_MAX_EXAMPLES:-12}"

AGENT_URL="${AGENT_SCHEMA_URL:-}"
GATEWAY_URL="${GATEWAY_SCHEMA_URL:-}"
LEGACY="${SCHEMA_URL:-}"

mkdir -p "$REPORT_DIR"

export SCHEMATHESIS_HOOKS="${SCHEMATHESIS_HOOKS:-tests.schemathesis_hooks}"

HEADER_ARGS=()
if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
  HEADER_ARGS+=( -H "Authorization: Bearer ${GATEWAY_LIVE_BEARER}" )
fi

run_one() {
  local location="$1"
  local junit_name="$2"
  local use_auth="${3:-0}"

  echo "Schemathesis run → ${location}"
  local auth_args=()
  if [[ "${use_auth}" == "1" ]] && [[ "${#HEADER_ARGS[@]}" -gt 0 ]]; then
    auth_args=( "${HEADER_ARGS[@]}" )
  fi

  uv run schemathesis run "${location}" \
    --wait-for-schema "${WAIT_FOR_SCHEMA_SECONDS}" \
    --report junit \
    --report-dir "${REPORT_DIR}" \
    --report-junit-path "${REPORT_DIR}/${junit_name}" \
    --checks "${CHECKS}" \
    --max-examples "${MAX_EX}" \
    --continue-on-failure \
    --exclude-path-regex '/ask/stream$' \
    --exclude-path '/ask/stream' \
    --exclude-path '/ask-stream' \
    ${auth_args[@]+"${auth_args[@]}"}
}

if [[ -n "${AGENT_URL}" ]]; then
  run_one "${AGENT_URL}" "junit-agent.xml" 0
fi

if [[ -n "${GATEWAY_URL}" ]]; then
  run_one "${GATEWAY_URL}" "junit-gateway.xml" 1
fi

if [[ -z "${AGENT_URL}" && -z "${GATEWAY_URL}" ]]; then
  if [[ -z "${LEGACY}" ]]; then
    echo "Set AGENT_SCHEMA_URL and/or GATEWAY_SCHEMA_URL (or legacy SCHEMA_URL)." >&2
    exit 1
  fi
  legacy_auth=0
  if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
    legacy_auth=1
  fi
  echo "Using legacy SCHEMA_URL (Bearer header only when GATEWAY_LIVE_BEARER is set)."
  run_one "${LEGACY}" "junit.xml" "${legacy_auth}"
fi

echo "Reports under: ${REPORT_DIR}"

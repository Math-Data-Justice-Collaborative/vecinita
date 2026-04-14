#!/usr/bin/env bash
# Live Schemathesis CLI against gateway and data-management APIs.
#
# Environment:
#   GATEWAY_SCHEMA_URL   — e.g. https://vecinita-gateway-lx27.onrender.com/api/v1/openapi.json
#   DATA_MANAGEMENT_SCHEMA_URL — e.g. https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json
#   GATEWAY_LIVE_BEARER  — optional Bearer token when ENABLE_AUTH=true on gateway
#   SCHEMATHESIS_CHECKS  — default: not_a_server_error
#   SCHEMATHESIS_REPORT_DIR — default: schemathesis-report (under cwd, usually backend/)
#   WAIT_FOR_SCHEMA_SECONDS — default: 30
#   SCHEMATHESIS_MAX_EXAMPLES — maps to --max-examples (default: 12)
#   SCHEMATHESIS_REQUEST_TIMEOUT — per-request HTTP timeout in seconds (default: 180)
#   SCHEMATHESIS_SOURCE_URL — optional; known source_url for GET /api/v1/documents/preview and
#       /download-url (hooks default: https://example.org/community-resource-guide). Set to a URL
#       that exists in the target Postgres to avoid 404 warnings on live runs.
#   SCHEMATHESIS_SCRAPE_JOB_ID — optional; UUID for GET /api/v1/scrape/{job_id} and POST …/cancel
#       (hooks default: example UUID). Set to a real job id from POST /api/v1/scrape when testing.
#   SCHEMATHESIS_SCRAPE_URL — optional; first URL in POST /api/v1/scrape body (default: https://example.com/page).
#   SCHEMATHESIS_INCLUDE_GATEWAY_REINDEX — set to 1 to include POST /api/v1/scrape/reindex in the gateway
#       run (default: excluded). Live fuzzing hits the gateway, which then calls REINDEX_SERVICE_URL on the
#       server; a bad or internal-only host yields 502 and fails not_a_server_error checks.
#
# Gateway deploy (Render) — reindex:
#   For POST /api/v1/scrape/reindex to succeed when included, configure the gateway's REINDEX_SERVICE_URL
#   to a publicly resolvable base URL (e.g. Modal scraper web URL) and REINDEX_TRIGGER_TOKEN to match
#   the scraper service. A 502 with "Name or service not known" means DNS cannot resolve the host
#   from the gateway container (fix in Render env / secrets).
set -euo pipefail

WAIT_FOR_SCHEMA_SECONDS="${WAIT_FOR_SCHEMA_SECONDS:-30}"
REPORT_DIR="${SCHEMATHESIS_REPORT_DIR:-schemathesis-report}"
CHECKS="${SCHEMATHESIS_CHECKS:-not_a_server_error}"
MAX_EX="${SCHEMATHESIS_MAX_EXAMPLES:-12}"
REQ_TIMEOUT="${SCHEMATHESIS_REQUEST_TIMEOUT:-180}"
MODEL_REQ_TIMEOUT="${SCHEMATHESIS_MODAL_MODEL_REQUEST_TIMEOUT:-300}"
MODEL_MAX_EX="${SCHEMATHESIS_MODAL_MODEL_MAX_EXAMPLES:-6}"

GATEWAY_URL="${GATEWAY_SCHEMA_URL:-https://vecinita-gateway-lx27.onrender.com/api/v1/openapi.json}"
DATA_MANAGEMENT_URL="${DATA_MANAGEMENT_SCHEMA_URL:-https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json}"

mkdir -p "$REPORT_DIR"

export SCHEMATHESIS_HOOKS="${SCHEMATHESIS_HOOKS:-tests.schemathesis_hooks}"

HEADER_ARGS=()
if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
  HEADER_ARGS+=( -H "Authorization: Bearer ${GATEWAY_LIVE_BEARER}" )
fi

_scraper_bearer_token() {
  if [[ -n "${SCRAPER_SCHEMATHESIS_BEARER:-}" ]]; then
    echo "${SCRAPER_SCHEMATHESIS_BEARER}"
    return
  fi
  if [[ -z "${SCRAPER_API_KEYS:-}" ]]; then
    echo ""
    return
  fi
  # First key in comma-separated SCRAPER_API_KEYS
  local raw first
  raw="${SCRAPER_API_KEYS%%,*}"
  first="${raw#"${raw%%[![:space:]]*}"}"
  first="${first%"${first##*[![:space:]]}"}"
  echo "${first}"
}

# Args: location, junit_name, use_gateway_bearer(0|1), request_timeout, max_examples, extra schemathesis args...
run_st() {
  local location="$1"
  local junit_name="$2"
  local use_gateway_auth="${3:-0}"
  local timeout_sec="${4:-$REQ_TIMEOUT}"
  local max_ex="${5:-$MAX_EX}"
  shift 5 || true

  echo "Schemathesis run → ${location}"
  local auth_args=()
  if [[ "${use_gateway_auth}" == "1" ]] && [[ "${#HEADER_ARGS[@]}" -gt 0 ]]; then
    auth_args=( "${HEADER_ARGS[@]}" )
  fi

  uv run schemathesis run "${location}" \
    --request-timeout "${timeout_sec}" \
    --wait-for-schema "${WAIT_FOR_SCHEMA_SECONDS}" \
    --report junit \
    --report-dir "${REPORT_DIR}" \
    --report-junit-path "${REPORT_DIR}/${junit_name}" \
    --checks "${CHECKS}" \
    --max-examples "${max_ex}" \
    --continue-on-failure \
    "${@}" \
    ${auth_args[@]+"${auth_args[@]}"}
}

run_core_openapi() {
  local location="$1"
  local junit_name="$2"
  local use_auth="${3:-0}"
  shift 3 || true
  local extra=("$@")
  local reindex_exclude=()
  if [[ "${SCHEMATHESIS_INCLUDE_GATEWAY_REINDEX:-0}" != "1" ]]; then
    reindex_exclude=( --exclude-path '/api/v1/scrape/reindex' )
  fi
  run_st "${location}" "${junit_name}" "${use_auth}" "${REQ_TIMEOUT}" "${MAX_EX}" \
    --exclude-path-regex '/ask/stream$' \
    --exclude-path '/ask/stream' \
    --exclude-path '/ask-stream' \
    "${reindex_exclude[@]+"${reindex_exclude[@]}"}" \
    "${extra[@]+"${extra[@]}"}"
}

if [[ -z "${GATEWAY_URL}" && -z "${DATA_MANAGEMENT_URL}" ]]; then
  echo "Set GATEWAY_SCHEMA_URL and/or DATA_MANAGEMENT_SCHEMA_URL." >&2
  exit 1
fi

if [[ -n "${GATEWAY_URL}" ]]; then
  run_core_openapi "${GATEWAY_URL}" "junit-gateway.xml" 1
fi

if [[ -n "${DATA_MANAGEMENT_URL}" ]]; then
  run_st "${DATA_MANAGEMENT_URL}" "junit-data-management.xml" 0 "${REQ_TIMEOUT}" "${MAX_EX}"
fi

echo "Reports under: ${REPORT_DIR}"

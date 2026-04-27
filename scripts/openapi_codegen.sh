#!/usr/bin/env bash
# Regenerate OpenAPI clients under packages/openapi-clients/ (FR-003).
# Requires: GATEWAY_SCHEMA_URL, DATA_MANAGEMENT_SCHEMA_URL, AGENT_SCHEMA_URL
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' <"$ROOT/scripts/openapi-generator-version.txt")"
CLI="@openapitools/openapi-generator-cli"

require_env() {
  local n="$1"
  if [[ -z "${!n:-}" ]]; then
    echo "openapi_codegen.sh: error: environment variable $n is not set" >&2
    exit 1
  fi
}

require_env GATEWAY_SCHEMA_URL
require_env DATA_MANAGEMENT_SCHEMA_URL
require_env AGENT_SCHEMA_URL

run_gen() {
  local label="$1" url="$2" generator="$3" out="$4"
  shift 4
  echo "==> openapi-generator [$label] -> $out ($generator)"
  (
    cd "$ROOT" && env NPM_CONFIG_PREFIX="${NPM_CONFIG_PREFIX:-/usr/local}" \
      npx --yes "$CLI" generate -i "$url" -g "$generator" -o "$out" "$@"
  )
}

echo "Using OpenAPI Generator version $VERSION (from scripts/openapi-generator-version.txt)"
(
  cd "$ROOT" && env NPM_CONFIG_PREFIX="${NPM_CONFIG_PREFIX:-/usr/local}" \
    npx --yes "$CLI" version-manager set "$VERSION" >/dev/null
)

# Python pydantic v1 clients
run_gen gateway "$GATEWAY_SCHEMA_URL" python-pydantic-v1 \
  "$ROOT/packages/openapi-clients/python/gateway" \
  --additional-properties=packageName=vecinita_openapi_gateway,library=urllib3

run_gen data_management "$DATA_MANAGEMENT_SCHEMA_URL" python-pydantic-v1 \
  "$ROOT/packages/openapi-clients/python/data_management" \
  --additional-properties=packageName=vecinita_openapi_data_management,library=urllib3

run_gen agent "$AGENT_SCHEMA_URL" python-pydantic-v1 \
  "$ROOT/packages/openapi-clients/python/agent" \
  --additional-properties=packageName=vecinita_openapi_agent,library=urllib3

# TypeScript Axios clients
run_gen gateway-ts-axios "$GATEWAY_SCHEMA_URL" typescript-axios \
  "$ROOT/packages/openapi-clients/typescript-axios/gateway" \
  --additional-properties=npmName=vecinita-gateway-openapi-axios,supportsES6=true,withInterfaces=true

run_gen data-management-ts-axios "$DATA_MANAGEMENT_SCHEMA_URL" typescript-axios \
  "$ROOT/packages/openapi-clients/typescript-axios/data_management" \
  --additional-properties=npmName=vecinita-data-management-openapi-axios,supportsES6=true,withInterfaces=true

run_gen agent-ts-axios "$AGENT_SCHEMA_URL" typescript-axios \
  "$ROOT/packages/openapi-clients/typescript-axios/agent" \
  --additional-properties=npmName=vecinita-agent-openapi-axios,supportsES6=true,withInterfaces=true

echo "openapi_codegen.sh: done"

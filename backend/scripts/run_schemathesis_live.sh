#!/usr/bin/env bash
set -euo pipefail

SCHEMA_URL="${SCHEMA_URL:-http://127.0.0.1:8004/api/v1/openapi.json}"
WAIT_FOR_SCHEMA_SECONDS="${WAIT_FOR_SCHEMA_SECONDS:-30}"
REPORT_DIR="${SCHEMATHESIS_REPORT_DIR:-schemathesis-report}"

mkdir -p "$REPORT_DIR"

export SCHEMATHESIS_HOOKS="${SCHEMATHESIS_HOOKS:-tests.schemathesis_hooks}"

uv run schemathesis run "$SCHEMA_URL" \
  --wait-for-schema "$WAIT_FOR_SCHEMA_SECONDS" \
  --report junit

echo "Schemathesis live run completed against: $SCHEMA_URL"
echo "Report directory: $REPORT_DIR"
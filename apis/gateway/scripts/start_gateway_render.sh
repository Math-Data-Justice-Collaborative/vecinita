#!/bin/sh

set -eu

exec uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}" \
  --timeout-graceful-shutdown 30
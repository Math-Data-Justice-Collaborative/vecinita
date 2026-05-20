#!/usr/bin/env bash
# Run Vecinita pytest via uv (workspace packages are not on bare PYTHONPATH).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required — https://docs.astral.sh/uv/" >&2
  exit 1
fi

uv sync --group dev

if [[ $# -eq 0 ]]; then
  set -- tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval
fi

exec uv run pytest "$@"

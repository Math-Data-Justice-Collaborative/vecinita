#!/usr/bin/env bash
# T13.3: ensure OpenAPI source-of-truth files exist and parse (api-contract.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPECS=(
  chat-rag.yaml
  data-management.yaml
  internal-write.yaml
)

for spec in "${SPECS[@]}"; do
  path="$ROOT/openapi/$spec"
  if [[ ! -f "$path" ]]; then
    echo "ERROR: missing $path" >&2
    exit 1
  fi
done

uv run python -c "
from pathlib import Path
import yaml
root = Path('openapi')
for name in ('chat-rag.yaml', 'data-management.yaml', 'internal-write.yaml'):
    yaml.safe_load((root / name).read_text())
print('OK: OpenAPI YAML files parse.')
"

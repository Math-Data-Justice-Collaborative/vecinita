#!/usr/bin/env bash
# Pre-deploy build smoke: deps sync, Modal app import, ADR-007 guard.
# Modal CLI has no `deploy --dry-run`; this is the CI/local substitute.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "==> uv sync"
uv sync --group dev

echo "==> ADR-007: no DATABASE_URL in Modal worker code"
bash scripts/check_modal_no_database_url.sh

echo "==> Modal SDK (deploy-time only; not in workspace lock)"
if ! uv run python -c "import modal" 2>/dev/null; then
  uv pip install 'modal>=1.2.6,<2'
fi

echo "==> Import Modal app modules (parse + image definition smoke)"
uv run python - <<'PY'
import importlib.util
from pathlib import Path

apps = [
    "infra/modal/embedding_app.py",
    "infra/modal/data_management_app.py",
    "infra/modal/llm_app.py",
]
for rel in apps:
    path = Path(rel)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {rel}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app"), f"{rel}: missing modal.App"
    print(f"OK import {rel}")
PY

echo "OK: verify_build passed (no live modal deploy — use verify_secrets.sh + operator deploy)."

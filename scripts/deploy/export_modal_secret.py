"""Export the live `vecinita-data-management` Modal secret to a gitignored dotenv.

Used by scripts/deploy/sync_modal_secret.sh --merge so that adding a single key
(e.g. EV-006 SUPABASE_SECRET_KEY) re-pushes the UNION of keys rather than
replacing the whole secret (`modal secret create --force` replaces, not merges).

Usage (from repo root, Modal auth in env):
  uv run --with modal modal run scripts/deploy/export_modal_secret.py
"""

from __future__ import annotations

import os
from pathlib import Path

import modal

BUNDLE_NAME = "vecinita-data-management"
# Only export application keys; never system/Modal-internal env vars.
PREFIXES = ("VECINITA_", "SUPABASE_")

app = modal.App("vecinita-secret-export-once")


@app.function(secrets=[modal.Secret.from_name(BUNDLE_NAME)])
def dump_secret_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k.startswith(PREFIXES)}


@app.local_entrypoint()
def main() -> None:
    data = dump_secret_env.remote()
    root = Path(__file__).resolve().parents[2]
    out = root / ".tmp" / f"modal-{BUNDLE_NAME}.env"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in sorted(data.items())]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.chmod(0o600)
    print(f"Wrote {out} keys={sorted(data)}")

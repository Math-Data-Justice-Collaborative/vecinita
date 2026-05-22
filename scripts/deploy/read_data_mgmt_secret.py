"""One-off: read vecinita-data-management secret into a local JSON file (gitignored).

Usage (from repo root, Modal auth in env):
  uv run --with modal modal run scripts/deploy/read_data_mgmt_secret.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import modal

KEYS = (
    "VECINITA_MODAL_EMBED_URL",
    "VECINITA_INTERNAL_WRITE_URL",
    "VECINITA_INTERNAL_API_KEY",
    "VECINITA_MODAL_PROXY_KEY",
    "VECINITA_CORS_ORIGINS",
)

app = modal.App("vecinita-secret-export-once")


@app.function(secrets=[modal.Secret.from_name("vecinita-data-management")])
def read_secret_env() -> dict[str, str]:
    return {k: os.environ.get(k, "") for k in KEYS}


@app.local_entrypoint()
def main() -> None:
    data = read_secret_env.remote()
    root = Path(__file__).resolve().parents[2]
    out = root / ".tmp" / "vecinita-data-management-secret.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(out, 0o600)
    missing = [k for k in KEYS if not data.get(k)]
    modal_len = len(data.get("VECINITA_MODAL_PROXY_KEY", ""))
    print(f"Wrote {out} modal_proxy_key_len={modal_len} missing={missing or 'none'}")

#!/usr/bin/env python3
"""Align Modal VECINITA_MODAL_PROXY_KEY with admin frontend bundle key.

Reads Modal secret via read_data_mgmt_secret (or existing .tmp JSON), extracts
the proxy key embedded in the live admin JS bundle, updates Modal secret if
different, then optionally syncs DO BUILD_TIME secret and triggers redeploy.

Usage:
  set -a && source prod.env && set +a
  uv run --with modal --with httpx scripts/deploy/sync_modal_proxy_key.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
SECRET_JSON = ROOT / ".tmp" / "vecinita-data-management-secret.json"
ADMIN_BUNDLE = (
    "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/assets/index-DQAu-JA9.js"
)
MODAL_JOBS = "https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs"
ADMIN_ORIGIN = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _bundle_modal_key() -> str:
    js = httpx.get(ADMIN_BUNDLE, timeout=60).text
    # First 48-char hex after Modal-Key header string in minified bundle
    marker = "Modal-Key"
    idx = js.find(marker)
    if idx >= 0:
        window = js[idx : idx + 400]
        for m in re.finditer(r"[a-f0-9]{48}", window):
            return m.group(0)
    # Fallback: hex near modalProxyKey / VITE_VECINITA_MODAL_PROXY_KEY patterns
    for m in re.finditer(r"[a-f0-9]{48}", js):
        start = max(0, m.start() - 120)
        ctx = js[start : m.end() + 40]
        if "modal" in ctx.lower() and "corpus" not in ctx.lower():
            return m.group(0)
    raise SystemExit("Could not locate Modal proxy key in admin bundle")


def _post_jobs(key: str) -> int:
    r = httpx.post(
        MODAL_JOBS,
        json={"urls": ["https://vecina.wrwc.org/"], "options": {"chunk_size_tokens": 256}},
        headers={
            "Content-Type": "application/json",
            "X-Vecinita-Proxy-Key": key,
            "Origin": ADMIN_ORIGIN,
        },
        timeout=60,
    )
    return r.status_code


def _load_modal_secret() -> dict[str, str]:
    if not SECRET_JSON.is_file():
        subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "modal",
                "modal",
                "run",
                "scripts/deploy/read_data_mgmt_secret.py",
            ],
            cwd=ROOT,
            check=True,
        )
    return json.loads(SECRET_JSON.read_text(encoding="utf-8"))


def _write_modal_secret(data: dict[str, str]) -> None:
    tmp = ROOT / ".tmp" / "vecinita-data-management-secret-new.json"
    tmp.write_text(json.dumps(data), encoding="utf-8")
    subprocess.run(
        [
            "modal",
            "secret",
            "create",
            "--force",
            "vecinita-data-management",
            "--from-json",
            str(tmp),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Update Modal secret and redeploy data-mgmt when keys differ",
    )
    parser.add_argument(
        "--sync-do",
        action="store_true",
        help="Also push VITE_VECINITA_MODAL_PROXY_KEY to DO and redeploy admin FE",
    )
    args = parser.parse_args()

    bundle_key = _bundle_modal_key()
    print(f"bundle_key sha256_prefix={_sha(bundle_key)} len={len(bundle_key)}")

    status = _post_jobs(bundle_key)
    print(f"POST /jobs with bundle key: status={status}")
    if status == 202:
        print("OK: keys already aligned — no change needed.")
        return 0

    secret = _load_modal_secret()
    modal_key = secret.get("VECINITA_MODAL_PROXY_KEY", "")
    print(f"modal_secret sha256_prefix={_sha(modal_key)} len={len(modal_key)}")
    if modal_key == bundle_key:
        print("Keys match in secret but POST still not 202 — investigate app/auth.")
        return 1

    if not args.apply:
        print("Dry run: would set VECINITA_MODAL_PROXY_KEY to bundle key and redeploy Modal.")
        return 0

    secret["VECINITA_MODAL_PROXY_KEY"] = bundle_key
    _write_modal_secret(secret)
    print("Updated Modal secret vecinita-data-management")

    subprocess.run(
        ["modal", "deploy", "infra/modal/data_management_app.py"],
        cwd=ROOT,
        check=True,
    )
    status = _post_jobs(bundle_key)
    print(f"POST /jobs after Modal redeploy: status={status}")
    if status != 202:
        return 1

    if args.sync_do:
        env = {**os.environ, "VITE_VECINITA_MODAL_PROXY_KEY": bundle_key}
        subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "pydo",
                "--with",
                "pyyaml",
                "scripts/deploy/do_apps.py",
                "sync-secrets",
                "--name",
                "vecinita-admin-frontend",
            ],
            cwd=ROOT,
            check=True,
            env=env,
        )
        subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "pydo",
                "--with",
                "pyyaml",
                "scripts/deploy/do_apps.py",
                "deploy",
                "--name",
                "vecinita-admin-frontend",
            ],
            cwd=ROOT,
            check=True,
            env=env,
        )
        print("DO admin frontend secrets synced and deploy triggered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

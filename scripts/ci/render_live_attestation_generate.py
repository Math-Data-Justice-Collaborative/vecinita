#!/usr/bin/env python3
"""Run Render preview live checks and write .ci/render-live-attestation.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TITLE_TOKEN = "[render preview]"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit("failed to resolve git HEAD")
    return proc.stdout.strip()


def _probe(url: str, timeout_seconds: float) -> tuple[bool, int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            body = resp.read(1024).decode("utf-8", errors="replace")
            return 200 <= resp.status < 400, resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read(1024).decode("utf-8", errors="replace")
        return False, int(exc.code), body
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        return False, 0, str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-base-url", required=True, help="Render preview service URL (https://...onrender.com)")
    parser.add_argument("--pr-title", required=True, help="PR title; must contain [render preview]")
    parser.add_argument(
        "--attestation",
        type=Path,
        default=Path(".ci/render-live-attestation.json"),
        help="Output attestation path.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Additional path to probe (repeatable), e.g. --path /api/v1/health",
    )
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args()

    if _TITLE_TOKEN not in args.pr_title.lower():
        raise SystemExit("PR title must include [render preview]")

    base = args.preview_base_url.rstrip("/")
    if not base.startswith("https://"):
        raise SystemExit("--preview-base-url must use https://")

    default_paths = ["/health", "/openapi.json"]
    extra_paths = [p if p.startswith("/") else f"/{p}" for p in args.path]
    paths = []
    for p in default_paths + extra_paths:
        if p not in paths:
            paths.append(p)

    checks: list[dict[str, Any]] = []
    all_ok = True
    for path in paths:
        url = f"{base}{path}"
        ok, status_code, snippet = _probe(url, args.timeout_seconds)
        checks.append(
            {
                "id": path.strip("/").replace("/", "-") or "root",
                "status": "passed" if ok else "failed",
                "url": url,
                "status_code": status_code,
                "notes": snippet[:240],
            }
        )
        if not ok:
            all_ok = False

    payload: dict[str, Any] = {
        "format_version": 1,
        "generated_at": _utc_now(),
        "git_head": _resolve_head(),
        "pr_title": args.pr_title,
        "preview_base_url": base,
        "status": "passed" if all_ok else "failed",
        "live_checks": checks,
    }
    args.attestation.parent.mkdir(parents=True, exist_ok=True)
    args.attestation.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

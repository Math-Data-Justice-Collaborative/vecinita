#!/usr/bin/env python3
"""
SC-001 smoke: run repeated create → list → get → cancel sequences against a live gateway.

Usage (from repo root)::

    python backend/scripts/smoke_modal_scraper_jobs.py \\
        --base-url https://<gateway-host> \\
        --iterations 100 \\
        --token \"$GATEWAY_BEARER_TOKEN\"

Exit code ``1`` if fewer than ``--min-success-rate`` (default 0.99) of iterations complete
without HTTP ``5xx`` responses on the modal scraper job endpoints.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from typing import Any

import httpx


def _headers(token: str) -> dict[str, str]:
    h: dict[str, str] = {"X-Correlation-ID": str(uuid.uuid4())}
    if token.strip():
        h["Authorization"] = f"Bearer {token.strip()}"
    return h


def _one_round(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[bool, str]:
    prefix = f"{base.rstrip('/')}/api/v1/modal-jobs/scraper"
    body: dict[str, Any] = {
        "url": "https://www.city.gov/housing/guide",
        "user_id": "smoke-modal-scraper",
        "crawl_config": {},
        "chunking_config": {},
        "metadata": {"source": "smoke_modal_scraper_jobs"},
    }
    r1 = client.post(prefix, json=body, headers=headers, timeout=120.0)
    if r1.status_code >= 500:
        return False, f"POST {prefix} -> {r1.status_code}"
    if r1.status_code not in (200, 201):
        return False, f"POST {prefix} -> {r1.status_code} {r1.text[:200]}"
    job_id = r1.json().get("job_id") or r1.json().get("id")
    if not job_id:
        return False, "POST missing job_id in JSON"

    r2 = client.get(prefix, headers=headers, timeout=60.0)
    if r2.status_code >= 500:
        return False, f"GET {prefix} -> {r2.status_code}"

    r3 = client.get(f"{prefix}/{job_id}", headers=headers, timeout=60.0)
    if r3.status_code >= 500:
        return False, f"GET {prefix}/{{id}} -> {r3.status_code}"

    r4 = client.post(f"{prefix}/{job_id}/cancel", headers=headers, timeout=60.0)
    if r4.status_code >= 500:
        return False, f"POST cancel -> {r4.status_code}"
    return True, "ok"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default=os.environ.get("SCHEMA_SMOKE_GATEWAY_URL", "").strip())
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--token", default=os.environ.get("GATEWAY_BEARER_TOKEN", "").strip())
    p.add_argument(
        "--min-success-rate",
        type=float,
        default=0.99,
        help="Minimum fraction of rounds without 5xx (default: 0.99 for SC-001).",
    )
    args = p.parse_args(argv)
    if not args.base_url:
        print("error: --base-url or SCHEMA_SMOKE_GATEWAY_URL is required", file=sys.stderr)
        return 2

    ok = 0
    failures: list[str] = []
    started = time.perf_counter()
    with httpx.Client(follow_redirects=True) as client:
        for i in range(args.iterations):
            hdr = _headers(args.token)
            good, msg = _one_round(client, args.base_url, hdr)
            if good:
                ok += 1
            else:
                failures.append(f"iter={i}: {msg}")
    elapsed = time.perf_counter() - started
    rate = ok / max(1, args.iterations)
    print(f"completed {ok}/{args.iterations} clean rounds in {elapsed:.1f}s (rate={rate:.4f})")
    if failures:
        print("failures (first 10):", file=sys.stderr)
        for line in failures[:10]:
            print(line, file=sys.stderr)
    if rate + 1e-9 < args.min_success_rate:
        print(
            f"error: success rate {rate:.4f} < required {args.min_success_rate:.4f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

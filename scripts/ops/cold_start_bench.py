#!/usr/bin/env python3
"""Opt-in cold-start latency harness (EV-314 / #314).

Forces Modal container cold (optional), runs N authenticated ``POST /generate`` samples,
emits JSON with p50/p95. Default ``--n 20`` (smoke); use ``--n 100`` to publish tails.

Synthetic prompt only — never pass user chat (ADR-004).

Examples::

    uv run python scripts/ops/cold_start_bench.py --n 20 --output /tmp/cold-smoke.json
    uv run python scripts/ops/cold_start_bench.py --n 100 --force-cold --output /tmp/cold-p95.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import httpx
from vecinita_shared_schemas.cold_start_latency import (
    summarize_latencies,
    validate_cold_start_sample,
)

_SYNTHETIC_PROMPT: Final[str] = "Context: pantry hours are 9am. Question: when is the pantry open?"
_DEFAULT_APP: Final[str] = "vecinita-llm"
_DEFAULT_ENV: Final[str] = "staging"
_PUBLISH_N: Final[int] = 100


def _proxy_headers(proxy_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Vecinita-Proxy-Key": proxy_key,
    }


def _post_generate(
    url: str,
    body: dict[str, object],
    *,
    headers: dict[str, str],
    timeout_s: float,
) -> None:
    response = httpx.post(url, json=body, headers=headers, timeout=timeout_s)
    _ = response.raise_for_status()


def _force_cold(*, app_name: str, environment: str) -> None:
    """Documented staging procedure: stop running containers so the next call restores cold."""
    cmd = [
        "modal",
        "container",
        "stop",
        "--env",
        environment,
        "--all",
        app_name,
    ]
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    _ = subprocess.run(cmd, check=False)


def _one_sample(
    *,
    generate_url: str,
    proxy_key: str,
    cold_kind: str,
    timeout_s: float,
) -> dict[str, object]:
    t0 = time.perf_counter()
    _post_generate(
        generate_url,
        {"prompt": _SYNTHETIC_PROMPT, "max_tokens": 8, "temperature": 0.0},
        headers=_proxy_headers(proxy_key),
        timeout_s=timeout_s,
    )
    first_token_ms = (time.perf_counter() - t0) * 1000.0
    sample = validate_cold_start_sample(
        {
            "cold_kind": cold_kind,
            "event": "first_token",
            "first_token_ms": first_token_ms,
        }
    )
    return dict(sample)


def main(argv: list[str] | None = None) -> int:
    """CLI entry — Layer E smoke / publish harness."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--n", type=int, default=20, help="Samples (default 20 smoke; 100 publish)"
    )
    _ = parser.add_argument(
        "--llm-url",
        default=os.environ.get("VECINITA_MODAL_LLM_URL", ""),
        help="Modal LLM base URL (or VECINITA_MODAL_LLM_URL)",
    )
    _ = parser.add_argument(
        "--proxy-key",
        default=os.environ.get("VECINITA_MODAL_PROXY_KEY", ""),
        help="Proxy key (or VECINITA_MODAL_PROXY_KEY)",
    )
    _ = parser.add_argument("--timeout-s", type=float, default=180.0)
    _ = parser.add_argument(
        "--cold-kind",
        default="snapshot_restore",
        choices=["warm", "snapshot_restore", "snapshot_create", "clean_boot"],
    )
    _ = parser.add_argument(
        "--force-cold",
        action="store_true",
        help="Run `modal container stop --all` before sampling (staging)",
    )
    _ = parser.add_argument("--modal-app", default=_DEFAULT_APP)
    _ = parser.add_argument(
        "--modal-env", default=os.environ.get("MODAL_ENVIRONMENT", _DEFAULT_ENV)
    )
    _ = parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    args = parser.parse_args(argv)

    if args.n < 1:
        print("--n must be >= 1", file=sys.stderr)
        return 2
    if not args.llm_url or not args.proxy_key:
        print("Need --llm-url and --proxy-key (or env)", file=sys.stderr)
        return 2

    if args.force_cold:
        _force_cold(app_name=args.modal_app, environment=args.modal_env)

    generate_url = f"{args.llm_url.rstrip('/')}/generate"
    samples: list[dict[str, object]] = []
    latencies: list[float] = []
    for index in range(args.n):
        if args.force_cold and index > 0:
            _force_cold(app_name=args.modal_app, environment=args.modal_env)
        try:
            sample = _one_sample(
                generate_url=generate_url,
                proxy_key=args.proxy_key,
                cold_kind=args.cold_kind,
                timeout_s=args.timeout_s,
            )
        except (httpx.HTTPError, TimeoutError, OSError) as exc:
            print(f"sample {index + 1}/{args.n} failed: {exc}", file=sys.stderr)
            return 1
        samples.append(sample)
        ft = sample.get("first_token_ms")
        if isinstance(ft, (int, float)):
            latencies.append(float(ft))
        print(f"sample {index + 1}/{args.n}: first_token_ms={ft}", file=sys.stderr)

    summary = summarize_latencies(latencies)
    report: dict[str, object] = {
        "n": args.n,
        "cold_kind": args.cold_kind,
        "publishable_p95": args.n >= _PUBLISH_N,
        "note": (
            "Statistical p95 requires n>=100 (AC-314-03). "
            "Do not conflate with prewarm_to_ready (#318)."
        ),
        "summary": summary,
        "samples": samples,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

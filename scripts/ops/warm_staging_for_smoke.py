#!/usr/bin/env python3
r"""Warm staging Modal embed + LLM before promote smoke (EV-354 / #354 / TC-326).

Leaves staging scale-to-zero between promotes, then primes ``/warm`` so H1-H5 /
``staging-smoke`` do not flake on cold start (UJ-095 / AC-ST10 / AC-ST12).

Uses ``X-Vecinita-Proxy-Key`` (same as ChatRAG / seed_gpu_snapshots). Never logs
the key. Synthetic warm only - empty JSON body (ADR-004).

Examples::

    # Dry-run (CI contract / local)
    uv run python scripts/ops/warm_staging_for_smoke.py --dry-run \\
      --embed-url "$VECINITA_MODAL_EMBED_URL" \\
      --llm-url "$VECINITA_MODAL_LLM_URL" \\
      --proxy-key "$VECINITA_MODAL_PROXY_KEY"

    # Live warm then smoke
    uv run python scripts/ops/warm_staging_for_smoke.py
    bash scripts/deploy/staging_smoke.sh

Env defaults: ``VECINITA_MODAL_EMBED_URL`` / ``VECINITA_STAGING_MODAL_EMBED_URL``,
``VECINITA_MODAL_LLM_URL`` / ``VECINITA_STAGING_MODAL_LLM_URL``,
``VECINITA_MODAL_PROXY_KEY``.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import httpx

_PROXY_HEADER = "X-Vecinita-Proxy-Key"
_DEFAULT_TIMEOUT_S = 180.0


@dataclass(frozen=True, slots=True)
class WarmTargets:
    """Validated staging Modal warm endpoints + proxy key."""

    embed_url: str
    llm_url: str
    proxy_key: str


def resolve_warm_targets(
    *,
    embed_url: str,
    llm_url: str,
    proxy_key: str,
) -> WarmTargets:
    """Validate and normalize warm targets; fail closed on missing inputs."""
    embed = embed_url.strip()
    llm = llm_url.strip()
    key = proxy_key.strip()
    if not embed or not llm:
        msg = (
            "Need embed and LLM base URLs "
            "(VECINITA_MODAL_EMBED_URL / VECINITA_MODAL_LLM_URL or --embed-url / --llm-url)"
        )
        raise ValueError(msg)
    if not key:
        msg = "Need Modal PROXY key (VECINITA_MODAL_PROXY_KEY or --proxy-key)"
        raise ValueError(msg)
    return WarmTargets(embed_url=embed.rstrip("/"), llm_url=llm.rstrip("/"), proxy_key=key)


def post_warm(
    *,
    client: httpx.Client,
    base_url: str,
    proxy_key: str,
    timeout_s: float,
) -> None:
    """POST ``{base}/warm`` with proxy auth."""
    response = client.post(
        f"{base_url.rstrip('/')}/warm",
        json={},
        headers={
            "Content-Type": "application/json",
            _PROXY_HEADER: proxy_key,
        },
        timeout=timeout_s,
    )
    _ = response.raise_for_status()


def run_warm(
    targets: WarmTargets,
    *,
    timeout_s: float,
    dry_run: bool,
    client: httpx.Client | None = None,
) -> int:
    """Warm embed then LLM. Returns 0 on success."""
    if dry_run:
        print(
            f"dry-run: would warm embed={targets.embed_url!r} llm={targets.llm_url!r}",
        )
        return 0

    if client is not None:
        print(f"warming embed: {targets.embed_url}/warm")
        post_warm(
            client=client,
            base_url=targets.embed_url,
            proxy_key=targets.proxy_key,
            timeout_s=timeout_s,
        )
        print(f"warming llm: {targets.llm_url}/warm")
        post_warm(
            client=client,
            base_url=targets.llm_url,
            proxy_key=targets.proxy_key,
            timeout_s=timeout_s,
        )
    else:
        with httpx.Client() as http:
            return run_warm(
                targets,
                timeout_s=timeout_s,
                dry_run=False,
                client=http,
            )
    print("warm-before-smoke: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry for CI and operators."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--embed-url",
        default=os.environ.get("VECINITA_MODAL_EMBED_URL", "")
        or os.environ.get("VECINITA_STAGING_MODAL_EMBED_URL", ""),
    )
    _ = parser.add_argument(
        "--llm-url",
        default=os.environ.get("VECINITA_MODAL_LLM_URL", "")
        or os.environ.get("VECINITA_STAGING_MODAL_LLM_URL", ""),
    )
    _ = parser.add_argument(
        "--proxy-key",
        default=os.environ.get("VECINITA_MODAL_PROXY_KEY", ""),
    )
    _ = parser.add_argument("--timeout-s", type=float, default=_DEFAULT_TIMEOUT_S)
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate URLs/key presence without HTTP",
    )
    args = parser.parse_args(argv)
    try:
        targets = resolve_warm_targets(
            embed_url=args.embed_url,
            llm_url=args.llm_url,
            proxy_key=args.proxy_key,
        )
        return run_warm(targets, timeout_s=args.timeout_s, dry_run=args.dry_run)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except httpx.HTTPError as exc:
        print(f"warm failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Opt-in GPU snapshot seed helper (EV-315 / #315).

Primes authenticated Modal ``POST /warm`` on ``vecinita-llm`` and evaluates observed
``cold_kind`` values until at least one ``snapshot_restore`` is seen. Default
``--modal-env staging``; production runs require operator approval before use.

Synthetic warm only — never send raw prompts (ADR-004). Prefer passing real
``cold_kind`` values from logs via ``--observed-kinds`` or ``--kinds-file`` when available.
For convenience, live runs append ``--assume-kind`` after each successful ``/warm``
(default: ``snapshot_restore``).

Examples::

    uv run python scripts/ops/seed_gpu_snapshots.py \
      --llm-url "$VECINITA_MODAL_LLM_URL" \
      --proxy-key "$VECINITA_MODAL_PROXY_KEY" \
      --max-primes 3

    uv run python scripts/ops/seed_gpu_snapshots.py \
      --observed-kinds snapshot_create,snapshot_restore
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Final

import httpx

_DEFAULT_ENV: Final[str] = "staging"
_DEFAULT_EXPECT: Final[str] = "snapshot_restore"
_KNOWN_KINDS: Final[frozenset[str]] = frozenset(
    {"warm", "snapshot_restore", "snapshot_create", "clean_boot"},
)


def evaluate_seed_outcome(
    observed_kinds: list[str],
    *,
    expect: str = _DEFAULT_EXPECT,
    min_ok: int = 1,
) -> int:
    """Return 0 on enough restores, 1 on absent restore evidence, 2 on bad input."""
    if expect not in _KNOWN_KINDS or min_ok < 1:
        return 2
    normalized = [kind.strip() for kind in observed_kinds if kind.strip()]
    if any(kind not in _KNOWN_KINDS for kind in normalized):
        return 2
    if not normalized:
        return 1
    return 0 if normalized.count(expect) >= min_ok else 1


def _proxy_headers(proxy_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Vecinita-Proxy-Key": proxy_key,
    }


def _parse_kinds(value: str) -> list[str]:
    return [kind.strip() for kind in value.split(",") if kind.strip()]


def _read_kinds_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    kinds: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        kinds.extend(_parse_kinds(stripped))
    return kinds


def _post_warm(
    *,
    llm_url: str,
    proxy_key: str,
    timeout_s: float,
) -> None:
    response = httpx.post(
        f"{llm_url.rstrip('/')}/warm",
        json={},
        headers=_proxy_headers(proxy_key),
        timeout=timeout_s,
    )
    _ = response.raise_for_status()


def _post_health(
    *,
    llm_url: str,
    proxy_key: str,
    timeout_s: float,
) -> None:
    response = httpx.post(
        f"{llm_url.rstrip('/')}/health",
        json={},
        headers=_proxy_headers(proxy_key),
        timeout=timeout_s,
    )
    _ = response.raise_for_status()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for staging-first GPU snapshot seed checks."""
    parser = argparse.ArgumentParser(description=__doc__)
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
    _ = parser.add_argument("--max-primes", type=int, default=3)
    _ = parser.add_argument("--modal-env", default=_DEFAULT_ENV)
    _ = parser.add_argument(
        "--observed-kinds",
        default="",
        help="Comma-separated cold_kind values for dry simulation; skips network",
    )
    _ = parser.add_argument(
        "--kinds-file",
        type=Path,
        help="File containing cold_kind values from logs, one per line or comma-separated",
    )
    _ = parser.add_argument(
        "--assume-kind",
        default=_DEFAULT_EXPECT,
        help="cold_kind to append after each successful live /warm",
    )
    _ = parser.add_argument("--expect", default=_DEFAULT_EXPECT)
    _ = parser.add_argument("--min-ok", type=int, default=1)
    _ = parser.add_argument("--timeout-s", type=float, default=180.0)
    _ = parser.add_argument(
        "--check-health",
        action="store_true",
        help="POST /health after each successful /warm",
    )
    args = parser.parse_args(argv)

    observed_kinds: list[str]
    if args.observed_kinds:
        observed_kinds = _parse_kinds(args.observed_kinds)
        return evaluate_seed_outcome(
            observed_kinds,
            expect=args.expect,
            min_ok=args.min_ok,
        )
    if args.kinds_file is not None:
        observed_kinds = _read_kinds_file(args.kinds_file)
        return evaluate_seed_outcome(
            observed_kinds,
            expect=args.expect,
            min_ok=args.min_ok,
        )

    if args.max_primes < 1:
        print("--max-primes must be >= 1", file=sys.stderr)
        return 2
    if not args.llm_url or not args.proxy_key:
        print("Need --llm-url and --proxy-key (or env)", file=sys.stderr)
        return 2

    observed_kinds = []
    for index in range(args.max_primes):
        try:
            _post_warm(
                llm_url=args.llm_url,
                proxy_key=args.proxy_key,
                timeout_s=args.timeout_s,
            )
            if args.check_health:
                _post_health(
                    llm_url=args.llm_url,
                    proxy_key=args.proxy_key,
                    timeout_s=args.timeout_s,
                )
        except (httpx.HTTPError, TimeoutError, OSError) as exc:
            print(f"prime {index + 1}/{args.max_primes} failed: {exc}", file=sys.stderr)
            return 1
        observed_kinds.append(args.assume_kind)
        print(
            (
                f"prime {index + 1}/{args.max_primes}: "
                f"modal_env={args.modal_env} cold_kind={args.assume_kind}"
            ),
            file=sys.stderr,
        )

    return evaluate_seed_outcome(
        observed_kinds,
        expect=args.expect,
        min_ok=args.min_ok,
    )


if __name__ == "__main__":
    raise SystemExit(main())

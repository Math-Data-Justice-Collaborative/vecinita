#!/usr/bin/env python3
r"""Opt-in GPU snapshot seed helper (EV-315 / #315).

Primes authenticated Modal ``POST /warm`` on ``vecinita-llm`` and evaluates observed
``cold_kind`` values until at least one ``snapshot_restore`` is seen. Default
``--modal-env staging``; production runs require operator approval before use.

Synthetic warm only — never send raw prompts (ADR-004).

Fail-closed (AC-315-01): a successful live ``/warm`` alone does **not** exit 0.
Pass restore evidence via ``--observed-kinds``, ``--kinds-file`` (raw logs or kinds),
or explicit opt-in ``--assume-kind`` (tests / documented override only).

Examples::

    # Prime only — exits 1 until kinds are supplied (still triggers captures)
    uv run python scripts/ops/seed_gpu_snapshots.py \
      --llm-url "$VECINITA_STAGING_MODAL_LLM_URL" \
      --proxy-key "$VECINITA_MODAL_PROXY_KEY" \
      --max-primes 3

    # Evaluate kinds pasted from Modal logs
    uv run python scripts/ops/seed_gpu_snapshots.py \
      --observed-kinds snapshot_create,snapshot_restore

    # Or parse a log capture file
    modal app logs vecinita-llm -e staging > /tmp/llm-logs.txt
    uv run python scripts/ops/seed_gpu_snapshots.py --kinds-file /tmp/llm-logs.txt
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Final

import httpx

_DEFAULT_ENV: Final[str] = "staging"
_DEFAULT_EXPECT: Final[str] = "snapshot_restore"
_KNOWN_KINDS: Final[frozenset[str]] = frozenset(
    {"warm", "snapshot_restore", "snapshot_create", "clean_boot"},
)
_KIND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"""['\"]cold_kind['\"]\s*:\s*['\"](\w+)['\"]"""),
    re.compile(r"""\bcold_kind=(\w+)\b"""),
)
_MODAL_RESTORE: Final[re.Pattern[str]] = re.compile(
    r"Restoring Function from memory snapshot",
    re.IGNORECASE,
)
_MODAL_CREATE: Final[re.Pattern[str]] = re.compile(
    r"Creat(?:ing|ed)(?: memory)? snapshot",
    re.IGNORECASE,
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


def parse_cold_kinds_from_log_text(text: str) -> list[str]:
    """Extract ``cold_kind`` values from Modal/app log text (order preserved).

    Accepts ``cold_start_stamp`` / ``cold_kind=`` tags and Modal platform lines
    (``Restoring Function from memory snapshot`` → ``snapshot_restore``;
    create snapshot lines → ``snapshot_create``).
    """
    found: list[str] = []
    for line in text.splitlines():
        matched_stamp = False
        for pattern in _KIND_PATTERNS:
            for match in pattern.finditer(line):
                kind = match.group(1)
                if kind in _KNOWN_KINDS:
                    found.append(kind)
                    matched_stamp = True
        if matched_stamp:
            continue
        if _MODAL_RESTORE.search(line):
            found.append("snapshot_restore")
        elif _MODAL_CREATE.search(line):
            found.append("snapshot_create")
    return found


def _proxy_headers(proxy_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Vecinita-Proxy-Key": proxy_key,
    }


def _parse_kinds(value: str) -> list[str]:
    return [kind.strip() for kind in value.split(",") if kind.strip()]


def read_kinds_file(path: Path) -> list[str]:
    """Read kinds from a file of CSV kinds or raw Modal logs."""
    raw = path.read_text(encoding="utf-8")
    parsed = parse_cold_kinds_from_log_text(raw)
    if parsed:
        return parsed
    # Plain kinds-only files (one kind or comma-separated per line) — not freeform logs
    kinds: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if " " in stripped and "cold_kind" not in stripped:
            # Likely a log/noise line without stamps — skip rather than invent kinds
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
        default=os.environ.get("VECINITA_MODAL_LLM_URL", "")
        or os.environ.get("VECINITA_STAGING_MODAL_LLM_URL", ""),
        help="Modal LLM base URL (or VECINITA_STAGING_MODAL_LLM_URL / VECINITA_MODAL_LLM_URL)",
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
        help="File with cold_kind values or raw Modal logs containing cold_start_stamp",
    )
    _ = parser.add_argument(
        "--assume-kind",
        default="",
        help=(
            "Opt-in only: append this cold_kind after each live /warm "
            "(tests/override — prefer --kinds-file from logs)"
        ),
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

    if args.observed_kinds:
        observed_kinds = _parse_kinds(args.observed_kinds)
        return evaluate_seed_outcome(
            observed_kinds,
            expect=args.expect,
            min_ok=args.min_ok,
        )
    if args.kinds_file is not None:
        observed_kinds = read_kinds_file(args.kinds_file)
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

    assume_kind = args.assume_kind.strip()
    if assume_kind and assume_kind not in _KNOWN_KINDS:
        print(f"unknown --assume-kind: {assume_kind!r}", file=sys.stderr)
        return 2

    observed_kinds: list[str] = []
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
        if assume_kind:
            observed_kinds.append(assume_kind)
        assume_suffix = f" assume_kind={assume_kind}" if assume_kind else ""
        msg = (
            f"prime {index + 1}/{args.max_primes}: "
            f"modal_env={args.modal_env} warm_ok{assume_suffix}"
        )
        print(msg, file=sys.stderr)

    if not observed_kinds:
        miss = (
            "no restore evidence: live /warm succeeded but cold_kind was not observed. "
            "Pass --kinds-file (Modal logs) or --observed-kinds, "
            "or opt-in --assume-kind for documented override only."
        )
        print(miss, file=sys.stderr)
        return 1

    return evaluate_seed_outcome(
        observed_kinds,
        expect=args.expect,
        min_ok=args.min_ok,
    )


if __name__ == "__main__":
    raise SystemExit(main())

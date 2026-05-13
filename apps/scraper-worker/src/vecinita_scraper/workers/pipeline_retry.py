"""Retry / backoff helpers for pipeline HTTP and transient failures (US2 / SC-003)."""

from __future__ import annotations

import os
from typing import Any


def sleep_before_retry_seconds(
    attempt_after_failure: int,
    *,
    base_seconds: float = 1.0,
    multiplier: float = 2.0,
    max_seconds: float = 32.0,
) -> float:
    """Sleep duration before retry ``attempt_after_failure`` (1-based after a failed try)."""
    if attempt_after_failure < 1:
        return 0.0
    delay = base_seconds * (multiplier ** (attempt_after_failure - 1))
    return float(min(max_seconds, delay))


def max_gateway_http_retries() -> int:
    raw = os.getenv("SCRAPER_GATEWAY_HTTP_MAX_RETRIES", "4").strip()
    try:
        n = int(raw)
    except ValueError:
        return 4
    return max(1, min(12, n))


def is_transient_http_status(status_code: int) -> bool:
    """Statuses where a retry may succeed (overload / transient upstream)."""
    return status_code in (408, 425, 429, 500, 502, 503, 504)


def gateway_retry_policy_from_env() -> dict[str, Any]:
    """Keyword args for :func:`sleep_before_retry_seconds` (overridable in tests)."""
    base = float(os.getenv("SCRAPER_GATEWAY_RETRY_BASE_SECONDS", "1.0") or 1.0)
    mult = float(os.getenv("SCRAPER_GATEWAY_RETRY_MULTIPLIER", "2.0") or 2.0)
    cap = float(os.getenv("SCRAPER_GATEWAY_RETRY_MAX_SECONDS", "32.0") or 32.0)
    return {
        "base_seconds": max(0.05, base),
        "multiplier": max(1.0, mult),
        "max_seconds": max(0.05, cap),
    }

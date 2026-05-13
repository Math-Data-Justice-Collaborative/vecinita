"""Guards for canonical corpus projection behavior."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def should_fail_closed_for_projection_error(exc: Exception) -> bool:
    """Fail closed for known canonical-path outages to avoid stale corpus views."""
    message = str(exc).lower()
    patterns = (
        "database_url_not_configured",
        "database_url is not configured",
        "could not connect to server",
        "connection refused",
        "timeout",
        "temporary failure in name resolution",
    )
    return any(pattern in message for pattern in patterns)


def sanitize_sources_for_fail_closed(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Suppress stale source payloads when a fail-closed path is triggered."""
    return [] if sources else sources


def _parse_visibility_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.min
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except Exception:
        return datetime.min


def reconcile_projection_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate per URL and keep the latest canonical visibility row."""
    by_url: dict[str, dict[str, Any]] = {}
    for source in sources:
        url = str(source.get("url") or "")
        if not url:
            continue
        existing = by_url.get(url)
        if existing is None:
            by_url[url] = source
            continue
        existing_ts = _parse_visibility_timestamp(existing.get("canonical_visibility_updated_at"))
        incoming_ts = _parse_visibility_timestamp(source.get("canonical_visibility_updated_at"))
        if incoming_ts >= existing_ts:
            by_url[url] = source
    return list(by_url.values())

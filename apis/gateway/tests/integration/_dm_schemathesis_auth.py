"""Shared auth probe for live Data Management (scraper) API Schemathesis tests."""

from __future__ import annotations

import os


def scraper_bearer_token() -> str | None:
    """Return first available scraper API bearer token, or ``None``."""
    direct = os.environ.get("SCRAPER_SCHEMATHESIS_BEARER", "").strip()
    if direct:
        return direct
    raw = os.environ.get("SCRAPER_API_KEYS", "").strip()
    if not raw:
        return None
    first = raw.split(",")[0].strip()
    return first or None

"""Validate SCRAPER_API_KEYS segments for Bearer auth + data-management frontend.

The data-management SPA stores one key and sends ``Authorization: Bearer <token>``.
The scraper API parses that header with a single whitespace split, so tokens must
not contain whitespace. Comma-separated env values must not embed commas inside
a single key segment.
"""

from __future__ import annotations


def iter_scraper_api_key_segment_errors(raw: str) -> list[str]:
    """Return human-readable errors for invalid segments; empty list if all valid."""
    errors: list[str] = []
    stripped = (raw or "").strip()
    if not stripped:
        return errors

    for idx, part in enumerate(stripped.split(",")):
        key = part.strip()
        seg = idx + 1
        if not key:
            errors.append(f"SCRAPER_API_KEYS segment {seg} is empty (remove extra commas).")
            continue
        if any(ch.isspace() for ch in key):
            errors.append(
                f"SCRAPER_API_KEYS segment {seg} contains whitespace; not compatible with "
                "Authorization: Bearer parsing or the data-management API key login."
            )
        if any(ord(ch) < 32 for ch in key):
            errors.append(
                f"SCRAPER_API_KEYS segment {seg} contains control characters; "
                "remove them for stable .env and HTTP header handling."
            )
    return errors

"""Document display title coalesce (F74 / ADR-051).

Citations, packing headers, and admin labels use
``COALESCE(display_title, title)`` — blank override falls back to scraped title.
"""

from __future__ import annotations


def coalesce_document_title(
    display_title: str | None,
    title: str | None,
) -> str | None:
    """Return operator display name when set; otherwise scraped ``title``."""
    if display_title is not None:
        cleaned = display_title.strip()
        if cleaned:
            return cleaned
    return title

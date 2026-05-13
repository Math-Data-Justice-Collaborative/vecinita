"""Static-first → Playwright escalation (US3)."""

from __future__ import annotations


def should_force_playwright(
    *,
    thin_body_chars: int,
    threshold: int,
    static_failed: bool,
) -> bool:
    if static_failed:
        return True
    return thin_body_chars < threshold

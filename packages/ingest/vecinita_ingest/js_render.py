"""JS-render policy helpers for scrape (F59 / ADR-045).

``VECINITA_SCRAPE_JS_RENDER`` is ``off`` | ``auto`` | ``always``. When ``auto`` or
``always``, the Modal DM worker runs Playwright Chromium (ADR-045); this module
only decides *whether* to escalate. Browser launch stays in the Modal image.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

_SPARSE_TEXT_CHARS: Final[int] = 80


class JsRenderMode(StrEnum):
    """``VECINITA_SCRAPE_JS_RENDER`` values."""

    OFF = "off"
    AUTO = "auto"
    ALWAYS = "always"


def parse_js_render_mode(value: str) -> JsRenderMode:
    """Parse config string into ``JsRenderMode``; raise ``ValueError`` if unknown."""
    normalized = value.strip().lower()
    try:
        return JsRenderMode(normalized)
    except ValueError as exc:
        msg = f"VECINITA_SCRAPE_JS_RENDER must be off|auto|always, got {value!r}"
        raise ValueError(msg) from exc


def should_js_render(*, mode: JsRenderMode, static_text: str) -> bool:
    """Decide whether to escalate from static HTML to Playwright."""
    if mode is JsRenderMode.OFF:
        return False
    if mode is JsRenderMode.ALWAYS:
        return True
    return len(static_text.strip()) < _SPARSE_TEXT_CHARS

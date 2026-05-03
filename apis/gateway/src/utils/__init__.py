"""Utilities module: centralized access to reusable utility helpers.

Heavy optional dependencies are imported lazily so lightweight helpers such as
tag normalization can be used in isolation during unit tests.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

__all__ = [
    "load_faqs_from_markdown",
    "reload_faqs",
    "get_faq_stats",
    "HTMLCleaner",
]

_LAZY_ATTR_MAP: dict[str, tuple[str, str]] = {
    "load_faqs_from_markdown": ("faq_loader", "load_faqs_from_markdown"),
    "reload_faqs": ("faq_loader", "reload_faqs"),
    "get_faq_stats": ("faq_loader", "get_faq_stats"),
    "HTMLCleaner": ("html_cleaner", "HTMLCleaner"),
}

if TYPE_CHECKING:
    from .faq_loader import get_faq_stats, load_faqs_from_markdown, reload_faqs
    from .html_cleaner import HTMLCleaner


def __getattr__(name: str) -> object:
    if name in _LAZY_ATTR_MAP:
        mod_name, attr_name = _LAZY_ATTR_MAP[name]
        mod = importlib.import_module(f"{__name__}.{mod_name}")
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Utilities module: centralized access to reusable utility helpers.

Heavy optional dependencies are imported lazily so lightweight helpers such as
tag normalization can be used in isolation during unit tests.
"""

from .faq_loader import get_faq_stats, load_faqs_from_markdown, reload_faqs
from .html_cleaner import HTMLCleaner

__all__ = [
    # FAQ utilities
    "load_faqs_from_markdown",
    "reload_faqs",
    "get_faq_stats",
    # HTML processing
    "HTMLCleaner",
]


def __getattr__(name: str) -> object:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

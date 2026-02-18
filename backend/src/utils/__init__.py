"""
Utilities module: Centralized, reusable utility functions and classes.

Exports:
- faq_loader: Markdown FAQ loading with caching
- html_cleaner: HTML boilerplate removal
- supabase_embeddings: Edge function embeddings wrapper
"""

from .faq_loader import (
    load_faqs_from_markdown,
    reload_faqs,
    get_faq_stats,
)
from .html_cleaner import HTMLCleaner
from .supabase_embeddings import SupabaseEmbeddings

__all__ = [
    # FAQ utilities
    "load_faqs_from_markdown",
    "reload_faqs",
    "get_faq_stats",
    # HTML processing
    "HTMLCleaner",
    # Embeddings
    "SupabaseEmbeddings",
]

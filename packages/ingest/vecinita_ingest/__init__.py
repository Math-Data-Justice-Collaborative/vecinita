"""Scrape and chunk helpers for corpus ingest."""

from vecinita_ingest.chunk import (
    DEFAULT_CHUNK_SIZE_TOKENS,
    MIN_CHUNK_SIZE_TOKENS,
    chunk_text,
    estimate_tokens,
)
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import fetch_url, parse_html

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CHUNK_SIZE_TOKENS",
    "MIN_CHUNK_SIZE_TOKENS",
    "ScrapedDocument",
    "chunk_text",
    "estimate_tokens",
    "fetch_url",
    "parse_html",
]

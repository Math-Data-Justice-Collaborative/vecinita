"""Scrape and chunk helpers for corpus ingest."""

from vecinita_ingest.chunk import (
    DEFAULT_CHUNK_OVERLAP_TOKENS,
    DEFAULT_CHUNK_SIZE_TOKENS,
    DEFAULT_CHUNK_TOKENIZER_ID,
    MIN_CHUNK_SIZE_TOKENS,
    chunk_text,
    count_tokens,
    encode_token_ids,
    estimate_tokens,
)
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import fetch_url, parse_html

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CHUNK_OVERLAP_TOKENS",
    "DEFAULT_CHUNK_SIZE_TOKENS",
    "DEFAULT_CHUNK_TOKENIZER_ID",
    "MIN_CHUNK_SIZE_TOKENS",
    "ScrapedDocument",
    "chunk_text",
    "count_tokens",
    "encode_token_ids",
    "estimate_tokens",
    "fetch_url",
    "parse_html",
]

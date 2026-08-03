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
from vecinita_ingest.js_render import JsRenderMode, parse_js_render_mode, should_js_render
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.pdf import PdfExtractError, extract_pdf_text
from vecinita_ingest.politeness import RateLimiter, robots_allows
from vecinita_ingest.scrape import extract_main_content, fetch_url, parse_html

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CHUNK_OVERLAP_TOKENS",
    "DEFAULT_CHUNK_SIZE_TOKENS",
    "DEFAULT_CHUNK_TOKENIZER_ID",
    "MIN_CHUNK_SIZE_TOKENS",
    "JsRenderMode",
    "PdfExtractError",
    "RateLimiter",
    "ScrapedDocument",
    "chunk_text",
    "count_tokens",
    "encode_token_ids",
    "estimate_tokens",
    "extract_main_content",
    "extract_pdf_text",
    "fetch_url",
    "parse_html",
    "parse_js_render_mode",
    "robots_allows",
    "should_js_render",
]

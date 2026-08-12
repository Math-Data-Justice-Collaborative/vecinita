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
from vecinita_ingest.crawl import CrawlPlan, CrawlResult, discover_crawl_urls, normalize_url
from vecinita_ingest.freshness import (
    UrlRefetchResult,
    content_hash_for_text,
    refetch_url_source,
)
from vecinita_ingest.js_render import JsRenderMode, parse_js_render_mode, should_js_render
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.nested_source import NestedSourceFields, derive_nested_source
from vecinita_ingest.pdf import PdfExtractError, extract_pdf_text
from vecinita_ingest.politeness import RateLimiter, robots_allows
from vecinita_ingest.scrape import extract_main_content, fetch_url, parse_html

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CHUNK_OVERLAP_TOKENS",
    "DEFAULT_CHUNK_SIZE_TOKENS",
    "DEFAULT_CHUNK_TOKENIZER_ID",
    "MIN_CHUNK_SIZE_TOKENS",
    "CrawlPlan",
    "CrawlResult",
    "JsRenderMode",
    "NestedSourceFields",
    "PdfExtractError",
    "RateLimiter",
    "ScrapedDocument",
    "UrlRefetchResult",
    "chunk_text",
    "content_hash_for_text",
    "count_tokens",
    "derive_nested_source",
    "discover_crawl_urls",
    "encode_token_ids",
    "estimate_tokens",
    "extract_main_content",
    "extract_pdf_text",
    "fetch_url",
    "normalize_url",
    "parse_html",
    "parse_js_render_mode",
    "refetch_url_source",
    "robots_allows",
    "should_js_render",
]

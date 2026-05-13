"""Unit tests for crawl outcome classification."""

from __future__ import annotations

import pytest

from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.classification import (
    finalize_html_crawled_page,
    map_crawl4ai_error_message,
    substantive_char_count,
)
from vecinita_scraper.crawlers.crawl4ai_adapter import CrawledPage


@pytest.mark.unit
def test_substantive_char_count_prefers_markdown() -> None:
    long_md = "word " * 50
    assert substantive_char_count(long_md, None, "<p>x</p>") >= 200


@pytest.mark.unit
def test_map_crawl4ai_error_message_detects_bot() -> None:
    assert (
        map_crawl4ai_error_message("Blocked by anti-bot protection: minimal_text")
        == FailureCategory.LIKELY_BOT_OR_CLIENT_LIMITATION
    )


@pytest.mark.unit
def test_finalize_marks_thin_success_as_failed() -> None:
    page = CrawledPage(
        url="https://example.com",
        markdown="short",
        html="<html></html>",
        cleaned_html="<html></html>",
        extracted_content=None,
        links=[],
        media=[],
        metadata={},
        content_hash="abc",
        status_code=200,
        success=True,
        error_message=None,
    )
    finalize_html_crawled_page(page)
    assert page.success is False
    assert page.failure_category is not None
    assert page.response_kind == ResponseKind.HTML


@pytest.mark.unit
def test_finalize_keeps_rich_success() -> None:
    body = "paragraph " * 30
    page = CrawledPage(
        url="https://example.com",
        markdown=body,
        html="<html></html>",
        cleaned_html=f"<main>{body}</main>",
        extracted_content=None,
        links=[],
        media=[],
        metadata={},
        content_hash="abc",
        status_code=200,
        success=True,
        error_message=None,
    )
    finalize_html_crawled_page(page)
    assert page.success is True
    assert page.failure_category is None

"""Unit tests for direct document fetch routing."""

from __future__ import annotations

import pytest

from vecinita_scraper.core.models import CrawlConfig
from vecinita_scraper.core.outcome_kinds import ResponseKind
from vecinita_scraper.crawlers.document_fetcher import try_direct_document_fetch


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_direct_returns_none_for_html(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_read(
        client: object, url: str, max_bytes: int
    ) -> tuple[bytes, int, str | None]:
        return (
            b"<!doctype html><html><body>Hi</body></html>",
            200,
            "text/html; charset=utf-8",
        )

    monkeypatch.setattr(
        "vecinita_scraper.crawlers.document_fetcher._read_body_capped",
        fake_read,
    )
    assert await try_direct_document_fetch("https://example.test/", CrawlConfig()) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_direct_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    body = ("Hello world. " * 30).encode("utf-8")

    async def fake_read(
        client: object, url: str, max_bytes: int
    ) -> tuple[bytes, int, str | None]:
        return body, 200, "text/plain; charset=utf-8"

    monkeypatch.setattr(
        "vecinita_scraper.crawlers.document_fetcher._read_body_capped",
        fake_read,
    )
    routed = await try_direct_document_fetch("https://example.test/readme.txt", CrawlConfig())
    assert routed is not None
    assert routed.response_kind == ResponseKind.PLAIN_TEXT
    assert routed.success is True
    assert len(routed.text.strip()) >= 200

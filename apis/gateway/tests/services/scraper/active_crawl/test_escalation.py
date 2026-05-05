"""Unit tests for static → Playwright escalation helper."""

from __future__ import annotations

from src.services.scraper.active_crawl.escalation import should_force_playwright


def test_should_force_playwright_on_static_failure() -> None:
    assert should_force_playwright(thin_body_chars=1000, threshold=400, static_failed=True) is True


def test_should_force_playwright_on_thin_body() -> None:
    assert should_force_playwright(thin_body_chars=10, threshold=400, static_failed=False) is True


def test_should_not_force_on_substantial_body() -> None:
    assert should_force_playwright(thin_body_chars=500, threshold=400, static_failed=False) is False

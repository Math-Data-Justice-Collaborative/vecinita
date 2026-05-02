"""Unit tests for live scraper URL normalization."""

from __future__ import annotations

import pytest

from src.services.scraper.active_crawl.live_scraper import normalize_jobs_base_url

pytestmark = pytest.mark.unit


def test_appends_jobs_when_missing() -> None:
    assert normalize_jobs_base_url("https://example.com") == "https://example.com/jobs"


def test_preserves_trailing_jobs() -> None:
    assert normalize_jobs_base_url("https://example.com/jobs") == "https://example.com/jobs"


def test_rejects_empty() -> None:
    with pytest.raises(ValueError):
        normalize_jobs_base_url("")

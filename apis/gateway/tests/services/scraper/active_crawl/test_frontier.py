"""Unit tests for crawl frontier."""

from __future__ import annotations

from src.services.scraper.active_crawl.frontier import CrawlFrontier, QueuedURL


def test_frontier_dedupes_and_respects_depth() -> None:
    f = CrawlFrontier(max_depth=1)
    assert f.enqueue(QueuedURL("https://a.com/", 0, "a.com")) is True
    assert f.enqueue(QueuedURL("https://a.com/", 0, "a.com")) is False
    assert f.enqueue(QueuedURL("https://a.com/b", 2, "a.com")) is False
    assert f.dequeue() == QueuedURL("https://a.com/", 0, "a.com")
    assert f.dequeue() is None

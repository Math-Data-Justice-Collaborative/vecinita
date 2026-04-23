"""Per-host robots.txt cache with optional dev override (FR-007)."""

from __future__ import annotations

import logging
import os
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger("vecinita_pipeline.active_crawl.robots")


class RobotsCache:
    def __init__(self, *, ignore_robots: bool) -> None:
        self.ignore = ignore_robots
        self._parsers: dict[str, RobotFileParser] = {}
        self._fetched: set[str] = set()

    def _base_url(self, url: str) -> str:
        p = urlparse(url)
        if not p.scheme or not p.netloc:
            return ""
        return f"{p.scheme}://{p.netloc}"

    def _ensure(self, base: str) -> RobotFileParser | None:
        if base in self._parsers:
            return self._parsers[base]
        if base in self._fetched:
            return self._parsers.get(base)
        self._fetched.add(base)
        robots_url = urljoin(base, "/robots.txt")
        rp = RobotFileParser()
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                r = client.get(robots_url)
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                else:
                    rp.parse(["User-agent: *", "Allow: /"])
        except Exception as exc:  # pragma: no cover - network
            log.warning("robots fetch failed for %s: %s — allowing all", robots_url, exc)
            rp.parse(["User-agent: *", "Allow: /"])
        self._parsers[base] = rp
        return rp

    def can_fetch(self, url: str, user_agent: str = "VecinaActiveCrawl/0.1") -> bool:
        if self.ignore:
            return True
        base = self._base_url(url)
        if not base:
            return False
        rp = self._ensure(base)
        if rp is None:
            return True
        try:
            return rp.can_fetch(user_agent, url)
        except Exception:
            return True


def robots_cache_from_env() -> RobotsCache:
    raw = (os.getenv("ACTIVE_CRAWL_IGNORE_ROBOTS") or "").strip().lower()
    ignore = raw in {"1", "true", "yes"}
    if ignore:
        log.warning(
            "ACTIVE_CRAWL_IGNORE_ROBOTS is set — robots.txt checks DISABLED (dev only, FR-007 exception)"
        )
    return RobotsCache(ignore_robots=ignore)

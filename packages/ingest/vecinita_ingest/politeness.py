"""Robots.txt and per-host rate limiting for polite scrape (F59)."""

from __future__ import annotations

import time
from urllib.robotparser import RobotFileParser


def robots_allows(*, robots_txt: str, url: str, user_agent: str) -> bool:
    """Return whether ``user_agent`` may fetch ``url`` per robots.txt body."""
    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, url)


class RateLimiter:
    """Sleep so successive ``wait()`` calls respect ``rate_limit_rps``."""

    def __init__(self, rate_limit_rps: float) -> None:
        """Initialize with requests-per-second cap (must be > 0)."""
        if rate_limit_rps <= 0:
            msg = "rate_limit_rps must be > 0"
            raise ValueError(msg)
        self._min_interval = 1.0 / rate_limit_rps
        self._last: float | None = None

    def wait(self) -> float:
        """Block until the next request is allowed; return seconds slept."""
        now = time.monotonic()
        if self._last is None:
            self._last = now
            return 0.0
        sleep_for = max(0.0, self._last + self._min_interval - now)
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last = time.monotonic()
        return sleep_for

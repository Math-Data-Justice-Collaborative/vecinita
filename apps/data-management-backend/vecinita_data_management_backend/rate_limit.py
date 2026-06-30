"""In-memory sliding-window rate limiter (EV-006 F35, ADR-030 §7).

Used to cap admin-triggered emails (invite 10/h, test-send 5/h) per admin JWT subject.
Sufficient for a small single-container operator team; not a distributed limiter.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class SlidingWindowRateLimiter:
    """Allow at most ``max_events`` per ``window_seconds`` for each key."""

    def __init__(
        self,
        *,
        max_events: int,
        window_seconds: float,
        now: Callable[[], float] | None = None,
    ) -> None:
        """Configure the budget; ``now`` is injectable for deterministic tests."""
        self._max = max_events
        self._window = window_seconds
        self._now = now or time.monotonic
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record an event for ``key`` and return whether it is within the budget."""
        now = self._now()
        events = self._events[key]
        cutoff = now - self._window
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self._max:
            return False
        events.append(now)
        return True

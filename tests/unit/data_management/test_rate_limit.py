"""EV-006 F35 (ADR-030 §7, TP-S005-07) — sliding-window invite rate limiter."""

from __future__ import annotations

from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter

_MAX = 2
_WINDOW = 60.0


class _Clock:
    """Manually-advanced monotonic clock for deterministic window tests."""

    def __init__(self) -> None:
        self.t = 1000.0

    def now(self) -> float:
        return self.t


def test_allows_up_to_limit_then_blocks() -> None:
    """The first N events pass; the (N+1)th within the window is blocked."""
    clock = _Clock()
    limiter = SlidingWindowRateLimiter(max_events=_MAX, window_seconds=_WINDOW, now=clock.now)
    assert limiter.allow("admin-1") is True
    assert limiter.allow("admin-1") is True
    assert limiter.allow("admin-1") is False


def test_window_expiry_frees_capacity() -> None:
    """Events older than the window no longer count against the limit."""
    clock = _Clock()
    limiter = SlidingWindowRateLimiter(max_events=_MAX, window_seconds=_WINDOW, now=clock.now)
    assert limiter.allow("admin-1") is True
    assert limiter.allow("admin-1") is True
    clock.t += _WINDOW + 1
    assert limiter.allow("admin-1") is True


def test_keys_are_independent() -> None:
    """Each key (admin) has its own independent budget."""
    clock = _Clock()
    limiter = SlidingWindowRateLimiter(max_events=_MAX, window_seconds=_WINDOW, now=clock.now)
    assert limiter.allow("admin-1") is True
    assert limiter.allow("admin-1") is True
    assert limiter.allow("admin-1") is False
    assert limiter.allow("admin-2") is True

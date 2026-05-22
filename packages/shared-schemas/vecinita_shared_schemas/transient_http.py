"""Transient upstream HTTP failures — shared retry policy for ChatRAG cold start."""

from __future__ import annotations

from typing import Final

COLD_START_ASK_MAX_ATTEMPTS: Final[int] = 3
COLD_START_ASK_RETRY_DELAY_S: Final[float] = 2.5

_TRANSIENT_ASK_STATUSES: Final[frozenset[int]] = frozenset({502, 503, 504})


def should_retry_ask(*, status_code: int | None, is_network_error: bool) -> bool:
    """Return True when a chat ask/stream request should be retried (Modal cold start)."""
    if is_network_error:
        return True
    if status_code is None:
        return False
    return status_code in _TRANSIENT_ASK_STATUSES

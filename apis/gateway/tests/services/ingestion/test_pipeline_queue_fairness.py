"""Contract: global FIFO claim order by ``created_at`` for equal-priority queued jobs (**FR-002**).

Workers implement the sort key in **T015** / **T022**; this module only pins the ordering rule
so backend tests do not import scraper worker packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class _QueuedJobRow:
    """Minimal row shape used to describe drain / claim ordering."""

    job_id: str
    created_at: datetime
    priority: int = 0


def claim_order_fifo_equal_priority(rows: list[_QueuedJobRow]) -> list[str]:
    """Return job ids in the order workers must claim them (FR-002 default).

    Sort key: ``(priority asc, created_at asc, job_id asc)`` — v1 uses only ``created_at`` when
    all priorities match (per ``data-model.md`` § Queue fairness).
    """
    ordered = sorted(rows, key=lambda r: (r.priority, r.created_at, r.job_id))
    return [r.job_id for r in ordered]


def test_fifo_by_created_at_when_priority_equal() -> None:
    t0 = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 4, 24, 12, 0, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 4, 24, 12, 0, 2, tzinfo=timezone.utc)
    rows = [
        _QueuedJobRow("late", t2, 0),
        _QueuedJobRow("first", t0, 0),
        _QueuedJobRow("mid", t1, 0),
    ]
    assert claim_order_fifo_equal_priority(rows) == ["first", "mid", "late"]


def test_higher_priority_preempts_older_created_at() -> None:
    """Document future extension: lower numeric priority value wins first (reserved)."""
    old = datetime(2026, 4, 24, 10, 0, 0, tzinfo=timezone.utc)
    new = datetime(2026, 4, 24, 11, 0, 0, tzinfo=timezone.utc)
    rows = [
        _QueuedJobRow("bulk", old, priority=1),
        _QueuedJobRow("vip", new, priority=0),
    ]
    assert claim_order_fifo_equal_priority(rows) == ["vip", "bulk"]

"""Unit tests for EvalRunEventBroker SSE helpers (EV-012 / T83.5 coverage)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

from vecinita_internal_write_api.eval_events import (
    EvalRunEventBroker,
    format_sse_eval_event,
    iter_eval_run_sse,
)

_RUN_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_RUN_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def test_publish_dedupes_identical_fingerprint() -> None:
    """Republishing the same run status does not append another event."""
    broker = EvalRunEventBroker()
    broker.publish(run_id=_RUN_A, status="pending")
    broker.publish(run_id=_RUN_A, status="pending")
    assert len(broker.events_after(None)) == 1


def test_events_after_invalid_last_id_replays_all() -> None:
    """Non-numeric Last-Event-ID replays the full buffer."""
    broker = EvalRunEventBroker()
    broker.publish(run_id=_RUN_A, status="running")
    assert len(broker.events_after("not-an-int")) == 1


def test_iter_eval_run_sse_skips_other_run_ids() -> None:
    """When sync_db is False, frames are filtered to the requested run_id."""
    broker = EvalRunEventBroker()
    broker.publish(run_id=_RUN_A, status="pending")
    broker.publish(run_id=_RUN_B, status="running")
    engine = MagicMock()
    frames = list(
        iter_eval_run_sse(
            engine,
            broker,
            run_id=_RUN_B,
            last_event_id=None,
            max_cycles=1,
            sync_db=False,
        )
    )
    assert len(frames) == 1
    assert str(_RUN_B) in frames[0]
    assert str(_RUN_A) not in frames[0]


def test_iter_eval_run_sse_stops_when_sync_db_missing() -> None:
    """sync_db path ends the iterator when the run is missing."""
    broker = EvalRunEventBroker()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.mappings.return_value.first.return_value = None
    frames = list(
        iter_eval_run_sse(
            engine,
            broker,
            run_id=_RUN_A,
            last_event_id=None,
            max_cycles=3,
            sync_db=True,
        )
    )
    assert frames == []


def test_format_sse_eval_event_shape() -> None:
    """format_sse_eval_event emits id/event/data trailer."""
    frame = format_sse_eval_event(event_id="9", payload_json='{"status":"pending"}')
    assert frame == 'id: 9\nevent: eval_run\ndata: {"status":"pending"}\n\n'


def test_events_after_empty_cursor_returns_all() -> None:
    """Empty string Last-Event-ID behaves like a fresh subscribe."""
    broker = EvalRunEventBroker()
    broker.publish(run_id=_RUN_A, status="completed")
    assert len(broker.events_after("")) == 1

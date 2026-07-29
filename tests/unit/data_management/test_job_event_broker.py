"""Unit tests for JobEventBroker SSE helpers (EV-012 / T82.2 coverage)."""

from __future__ import annotations

from uuid import uuid4

from vecinita_data_management_backend.job_events import (
    JobEventBroker,
    format_sse_job_event,
    iter_job_sse,
)
from vecinita_data_management_backend.store import InMemoryJobStore


def test_format_sse_job_event_includes_id_event_data() -> None:
    """SSE frame uses id, event: job, and data payload."""
    frame = format_sse_job_event(event_id="3", payload_json='{"job_id":"x"}')
    assert frame.startswith("id: 3\n")
    assert "event: job\n" in frame
    assert 'data: {"job_id":"x"}\n\n' in frame


def test_broker_skips_unchanged_fingerprint() -> None:
    """sync_from_store does not republish identical job state."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    broker = JobEventBroker()
    broker.sync_from_store(store)
    first = broker.events_after(None)
    assert len(first) == 1
    broker.sync_from_store(store)
    assert broker.events_after(None) == first
    store.update_job(record.job_id, status="running")
    broker.sync_from_store(store)
    after_update = broker.events_after(None)
    assert len(after_update) == len(first) + 1


def test_events_after_invalid_last_id_returns_all() -> None:
    """Non-numeric Last-Event-ID falls back to full history."""
    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com/a"])
    broker = JobEventBroker()
    broker.sync_from_store(store)
    assert len(broker.events_after("not-a-number")) == 1
    assert broker.events_after("") == broker.events_after(None)


def test_iter_job_sse_respects_max_cycles() -> None:
    """max_cycles bounds the poll loop for finite streams."""
    store = InMemoryJobStore()
    store.create_job(urls=[f"https://example.com/{uuid4()}"])
    broker = JobEventBroker()
    frames = list(
        iter_job_sse(
            store,
            broker,
            last_event_id=None,
            poll_interval_s=0.0,
            max_cycles=1,
        )
    )
    assert len(frames) == 1
    assert "event: job" in frames[0]

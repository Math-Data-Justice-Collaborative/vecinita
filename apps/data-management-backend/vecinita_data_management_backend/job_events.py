"""SSE job event broker for GET /jobs/events (EV-012 / TP-S013-01)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING

from vecinita_data_management_backend.store import job_record_to_schema

if TYPE_CHECKING:
    from collections.abc import Iterator

    from vecinita_data_management_backend.store import JobRecord, JobStore


@dataclass
class _BrokerEvent:
    event_id: str
    fingerprint: str
    payload_json: str


@dataclass
class JobEventBroker:
    """Process-local ordered job events for SSE framing + Last-Event-ID reconnect."""

    _seq: int = 0
    _events: list[_BrokerEvent] = field(default_factory=list)
    _fingerprints: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def sync_from_store(self, store: JobStore) -> None:
        """Publish events for jobs whose fingerprint changed since last sync."""
        for record in store.list_jobs():
            self._maybe_publish(record)

    def _fingerprint(self, record: JobRecord) -> str:
        return f"{record.job_id}:{record.status}:{record.updated_at.isoformat()}"

    def _maybe_publish(self, record: JobRecord) -> None:
        fingerprint = self._fingerprint(record)
        job_key = str(record.job_id)
        with self._lock:
            if self._fingerprints.get(job_key) == fingerprint:
                return
            self._seq += 1
            event_id = str(self._seq)
            schema = job_record_to_schema(record)
            payload_json = json.dumps(schema.model_dump(mode="json"), separators=(",", ":"))
            self._events.append(
                _BrokerEvent(event_id=event_id, fingerprint=fingerprint, payload_json=payload_json)
            )
            self._fingerprints[job_key] = fingerprint

    def events_after(self, last_event_id: str | None) -> list[_BrokerEvent]:
        """Return events strictly after ``last_event_id`` (numeric sequence)."""
        with self._lock:
            if last_event_id is None or last_event_id == "":
                return list(self._events)
            try:
                last_n = int(last_event_id)
            except ValueError:
                return list(self._events)
            return [event for event in self._events if int(event.event_id) > last_n]


def format_sse_job_event(*, event_id: str, payload_json: str) -> str:
    """Format one SSE job event block (id + event + data)."""
    return f"id: {event_id}\nevent: job\ndata: {payload_json}\n\n"


def iter_job_sse(
    store: JobStore,
    broker: JobEventBroker,
    *,
    last_event_id: str | None,
    poll_interval_s: float = 0.25,
    max_cycles: int | None = None,
) -> Iterator[str]:
    """Yield SSE frames; sync store → broker then poll for updates.

    ``max_cycles`` bounds the poll loop (tests); ``None`` means run until client disconnect.
    """
    cursor = last_event_id
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        broker.sync_from_store(store)
        for event in broker.events_after(cursor):
            yield format_sse_job_event(event_id=event.event_id, payload_json=event.payload_json)
            cursor = event.event_id
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
        time.sleep(poll_interval_s)

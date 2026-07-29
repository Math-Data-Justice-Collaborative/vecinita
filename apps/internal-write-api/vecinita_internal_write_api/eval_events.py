"""SSE eval-run progress broker for GET …/eval/runs/{id}/events (EV-012 / TP-S013-04)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import mapping_row, row_str

if TYPE_CHECKING:
    from collections.abc import Iterator
    from uuid import UUID

    from sqlalchemy.engine import Engine


@dataclass
class EvalRunBrokerEvent:
    """One ordered SSE payload for an eval run status snapshot."""

    event_id: str
    fingerprint: str
    payload_json: str


@dataclass
class EvalRunEventBroker:
    """Process-local ordered eval-run events for SSE framing + Last-Event-ID reconnect."""

    _seq: int = 0
    _events: list[EvalRunBrokerEvent] = field(default_factory=list)
    _fingerprints: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def publish(self, *, run_id: UUID, status: str) -> None:
        """Publish a status snapshot when the fingerprint changes."""
        fingerprint = f"{run_id}:{status}"
        run_key = str(run_id)
        with self._lock:
            if self._fingerprints.get(run_key) == fingerprint:
                return
            self._seq += 1
            event_id = str(self._seq)
            payload_json = json.dumps(
                {"run_id": str(run_id), "status": status},
                separators=(",", ":"),
            )
            self._events.append(
                EvalRunBrokerEvent(
                    event_id=event_id,
                    fingerprint=fingerprint,
                    payload_json=payload_json,
                )
            )
            self._fingerprints[run_key] = fingerprint

    def sync_from_engine(self, engine: Engine, *, run_id: UUID) -> bool:
        """Load current status from Postgres; return False if missing/soft-deleted."""
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT status FROM eval_runs
                        WHERE id = :id AND deleted_at IS NULL
                        """
                    ),
                    {"id": run_id},
                )
                .mappings()
                .first()
            )
        if row is None:
            return False
        status = row_str(mapping_row(row), "status")
        self.publish(run_id=run_id, status=status)
        return True

    def events_after(self, last_event_id: str | None) -> list[EvalRunBrokerEvent]:
        """Return events strictly after ``last_event_id`` (numeric sequence)."""
        with self._lock:
            if last_event_id is None or last_event_id == "":
                return list(self._events)
            try:
                last_n = int(last_event_id)
            except ValueError:
                return list(self._events)
            return [event for event in self._events if int(event.event_id) > last_n]


def format_sse_eval_event(*, event_id: str, payload_json: str) -> str:
    """Format one SSE eval_run event block (id + event + data)."""
    return f"id: {event_id}\nevent: eval_run\ndata: {payload_json}\n\n"


def iter_eval_run_sse(  # noqa: PLR0913  # SSE loop needs engine, broker, cursor, poll bounds
    engine: Engine,
    broker: EvalRunEventBroker,
    *,
    run_id: UUID,
    last_event_id: str | None,
    poll_interval_s: float = 0.25,
    max_cycles: int | None = None,
    sync_db: bool = True,
) -> Iterator[str]:
    """Yield SSE frames for one eval run; optionally sync DB → broker then poll."""
    cursor = last_event_id
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        if sync_db and not broker.sync_from_engine(engine, run_id=run_id):
            return
        for event in broker.events_after(cursor):
            if f'"run_id":"{run_id}"' not in event.payload_json:
                continue
            yield format_sse_eval_event(event_id=event.event_id, payload_json=event.payload_json)
            cursor = event.event_id
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
        time.sleep(poll_interval_s)

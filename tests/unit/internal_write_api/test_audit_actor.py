"""Unit tests for request-scoped audit actor binding (EV-005, no external DB)."""

from __future__ import annotations

from uuid import uuid4

from vecinita_internal_write_api.audit import (
    bind_audit_actor,
    clear_audit_actor,
    emit_audit_event,
)


class _RecordingConnection:
    """Minimal SQLAlchemy Connection stub that records execute() parameters."""

    def __init__(self) -> None:
        self.params: dict[str, object] = {}

    def execute(self, statement: object, parameters: dict[str, object]) -> None:
        """Record the bound parameters of the audit INSERT."""
        _ = statement
        self.params = parameters


def test_bind_and_clear_audit_actor_round_trip() -> None:
    """bind_audit_actor sets the context actor; emit uses it; clear resets it."""
    actor_id = uuid4()
    bind_audit_actor(actor_id=actor_id, actor_role="admin")
    try:
        conn = _RecordingConnection()
        emit_audit_event(
            conn,  # type: ignore[arg-type]
            event_type="document.updated",
            entity_type="document",
            entity_id=uuid4(),
            request_id=uuid4(),
        )
        assert conn.params["actor_id"] == actor_id
        assert conn.params["actor_role"] == "admin"
    finally:
        clear_audit_actor()

    conn = _RecordingConnection()
    emit_audit_event(
        conn,  # type: ignore[arg-type]
        event_type="document.updated",
        entity_type="document",
        entity_id=uuid4(),
        request_id=uuid4(),
    )
    assert conn.params["actor_id"] is None
    assert conn.params["actor_role"] is None


def test_emit_audit_event_prefers_explicit_actor_over_context() -> None:
    """An explicitly-passed actor bypasses the request-scoped context lookup (56->58)."""
    bind_audit_actor(actor_id=uuid4(), actor_role="viewer")
    try:
        explicit_id = uuid4()
        conn = _RecordingConnection()
        emit_audit_event(
            conn,  # type: ignore[arg-type]
            event_type="document.deleted",
            entity_type="document",
            entity_id=uuid4(),
            request_id=uuid4(),
            actor_id=explicit_id,
            actor_role="admin",
        )
        assert conn.params["actor_id"] == explicit_id
        assert conn.params["actor_role"] == "admin"
    finally:
        clear_audit_actor()

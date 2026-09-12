"""Scheduled catch-up tick records automation_runs (TC-289 / ADR-052).

[Corpus: feature-list.md §F78]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-289]
[Spec: docs/acceptance-criteria.md §AC-AU5 AC-AU7]
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from vecinita_data_management_backend.schedule_catchup import (
    record_scheduled_catchup_tick,
    run_scheduled_catchup_tick,
)
from vecinita_shared_schemas.automations import AutomationsConfigResponse

if TYPE_CHECKING:
    import pytest

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


class _RecordingWriteClient:
    def __init__(self, *, db_enabled: bool = True) -> None:
        self.calls: list[dict[str, object]] = []
        self.db_enabled = db_enabled

    def record_automation_run(self, **kwargs: object) -> UUID:
        self.calls.append(dict(kwargs))
        return uuid4()

    def get_automations_config(self) -> AutomationsConfigResponse:
        return AutomationsConfigResponse(
            enabled=self.db_enabled,
            kill_switch=False,
            max_concurrent=2,
        )


def test_scheduled_catchup_tick_records_completed_run() -> None:
    """Daily catch-up tick persists a run row even when no residual enqueue."""
    client = _RecordingWriteClient()
    result = record_scheduled_catchup_tick(client)
    assert result == "automation_catchup_tick"
    assert client.calls == [
        {
            "job_type": "automation_catchup",
            "status": "completed",
            "document_id": None,
            "revision": None,
            "error": None,
        }
    ]


def test_scheduled_catchup_tick_survives_missing_recorder() -> None:
    """Tick still returns when write client has no persist method."""

    class _BareClient:
        pass

    result = record_scheduled_catchup_tick(_BareClient())
    assert result == "automation_catchup_tick"


def test_scheduled_catchup_tick_scans_residuals_and_enqueues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-341 / AC-AU8: daily tick scans residuals and enqueues under real gates."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_MAX_CONCURRENT", "2")
    write = _RecordingWriteClient()
    enqueued: list[tuple[UUID, str, str]] = []

    def enqueue(document_id: UUID, *, revision: str, embed_status: str) -> UUID:
        enqueued.append((document_id, revision, embed_status))
        return uuid4()

    result = run_scheduled_catchup_tick(
        write_client=write,
        list_residuals=lambda: [(DOC_ID, "rev-1", "missing"), (uuid4(), "rev-2", "partial")],
        enqueue_catchup=enqueue,
        running_count=1,
        seen_keys=frozenset({f"{DOC_ID}:rev-1"}),
    )

    assert len(enqueued) == 1
    assert enqueued[0][1:] == ("rev-2", "partial")
    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 1,
        "skipped": 1,
        "outcome": "enqueued",
    }
    assert write.calls == [
        {
            "job_type": "automation_catchup",
            "status": "completed",
            "document_id": None,
            "revision": None,
            "error": None,
        }
    ]


def test_scheduled_catchup_tick_records_failed_when_history_persist_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-343 / AC-AU10: history persist failure is visible in the tick summary."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")

    class _FailingWriteClient:
        def record_automation_run(self, **kwargs: object) -> UUID:
            _ = kwargs
            msg = "write api down"
            raise RuntimeError(msg)

        def get_automations_config(self) -> AutomationsConfigResponse:
            return AutomationsConfigResponse(
                enabled=True,
                kill_switch=False,
                max_concurrent=2,
            )

    result = run_scheduled_catchup_tick(
        write_client=_FailingWriteClient(),
        list_residuals=list,
        enqueue_catchup=_return_document_id,
        running_count=0,
        seen_keys=frozenset(),
    )

    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "history_persist_failed",
        "history_persist_failed": True,
    }


def _return_document_id(
    document_id: UUID,
    *,
    revision: str,
    embed_status: str,
) -> UUID:
    _ = (revision, embed_status)
    return document_id


def test_scheduled_catchup_tick_skips_on_kill_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kill-switch → blocked tick with zero enqueue (TC-253)."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    write = _RecordingWriteClient()

    result = run_scheduled_catchup_tick(
        write_client=write,
        list_residuals=lambda: [(DOC_ID, "rev-1", "missing")],
        enqueue_catchup=_return_document_id,
        running_count=0,
        seen_keys=frozenset(),
    )

    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_kill_switch",
    }
    assert write.calls == [
        {
            "job_type": "automation_catchup",
            "status": "blocked",
            "document_id": None,
            "revision": None,
            "error": None,
        }
    ]


def test_scheduled_catchup_tick_kill_switch_history_persist_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-343: kill-switch tick surfaces history_persist_failed when write API fails."""

    class _FailingWriteClient:
        def record_automation_run(self, **kwargs: object) -> UUID:
            _ = kwargs
            msg = "write api down"
            raise RuntimeError(msg)

    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    result = run_scheduled_catchup_tick(
        write_client=_FailingWriteClient(),
        list_residuals=list,
        enqueue_catchup=_return_document_id,
        running_count=0,
        seen_keys=frozenset(),
    )

    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_kill_switch",
        "history_persist_failed": True,
    }


def test_scheduled_catchup_tick_skips_when_automations_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Master automations disabled → skipped tick without enqueue."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    write = _RecordingWriteClient()

    def _fail_if_called(document_id: UUID, *, revision: str, embed_status: str) -> UUID:
        _ = (document_id, revision, embed_status)
        msg = "enqueue should not run when automations disabled"
        raise AssertionError(msg)

    result = run_scheduled_catchup_tick(
        write_client=write,
        list_residuals=lambda: [(DOC_ID, "rev-1", "missing")],
        enqueue_catchup=_fail_if_called,
        running_count=0,
        seen_keys=frozenset(),
    )
    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_disabled",
    }
    assert write.calls == [
        {
            "job_type": "automation_catchup",
            "status": "skipped",
            "document_id": None,
            "revision": None,
            "error": None,
        }
    ]


def test_scheduled_catchup_tick_skips_when_db_automations_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU1: DM UI disable (DB) blocks scheduled residual enqueue even if env on."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    write = _RecordingWriteClient(db_enabled=False)

    def _fail_if_called(document_id: UUID, *, revision: str, embed_status: str) -> UUID:
        _ = (document_id, revision, embed_status)
        msg = "enqueue should not run when DB automations disabled"
        raise AssertionError(msg)

    result = run_scheduled_catchup_tick(
        write_client=write,
        list_residuals=lambda: [(DOC_ID, "rev-1", "missing")],
        enqueue_catchup=_fail_if_called,
        running_count=0,
        seen_keys=frozenset(),
    )
    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_disabled",
    }
    assert write.calls == [
        {
            "job_type": "automation_catchup",
            "status": "skipped",
            "document_id": None,
            "revision": None,
            "error": None,
        }
    ]


def test_scheduled_catchup_tick_disabled_history_persist_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disabled tick surfaces history_persist_failed when write API fails."""

    class _FailingWriteClient:
        def record_automation_run(self, **kwargs: object) -> UUID:
            _ = kwargs
            msg = "write api down"
            raise RuntimeError(msg)

    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    result = run_scheduled_catchup_tick(
        write_client=_FailingWriteClient(),
        list_residuals=list,
        enqueue_catchup=_return_document_id,
        running_count=0,
        seen_keys=frozenset(),
    )

    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_disabled",
        "history_persist_failed": True,
    }


def test_scheduled_catchup_tick_noop_when_nothing_enqueued(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All residuals deduped/skipped → outcome=noop."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    write = _RecordingWriteClient()

    result = run_scheduled_catchup_tick(
        write_client=write,
        list_residuals=lambda: [(DOC_ID, "rev-1", "missing")],
        enqueue_catchup=_return_document_id,
        running_count=0,
        seen_keys=frozenset({f"{DOC_ID}:rev-1"}),
    )

    assert result == {
        "job_type": "automation_catchup",
        "enqueued": 0,
        "skipped": 1,
        "outcome": "noop",
    }

"""Scheduled catch-up tick records automation_runs (TC-289 / ADR-052).

[Corpus: feature-list.md §F78]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-289]
[Spec: docs/acceptance-criteria.md §AC-AU5 AC-AU7]
"""

from __future__ import annotations

from uuid import UUID, uuid4

from vecinita_data_management_backend.schedule_catchup import record_scheduled_catchup_tick


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def record_automation_run(self, **kwargs: object) -> UUID:
        self.calls.append(dict(kwargs))
        return uuid4()


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

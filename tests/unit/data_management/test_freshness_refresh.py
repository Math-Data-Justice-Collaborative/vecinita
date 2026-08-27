"""T128.4 — F76 Modal freshness_refresh worker + shared schedule branch.

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/test-plan.md §TC-256-TC-259 §TC-264]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP2]
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from vecinita_data_management_backend.freshness_refresh import (
    run_freshness_refresh_job,
    run_scheduled_freshness_tick,
)
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.data_management import CreateJobRequest
from vecinita_shared_schemas.internal_write import DocumentSummary

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
DOC_ID_2 = UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")
_NOW = datetime(2026, 8, 12, 12, 0, 0, tzinfo=UTC)


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


class _StubWriteClient:
    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _StubWriteClient:
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        _ = event


def _freshness_options(
    *,
    document_id: UUID = DOC_ID,
    force: bool = False,
    refresh_enabled: bool = True,
    is_stale: bool = True,
) -> dict[str, object]:
    return {
        "document_id": str(document_id),
        "force": force,
        "refresh_enabled": refresh_enabled,
        "is_stale": is_stale,
    }


def test_freshness_worker_kill_switch_skips_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared kill-switch → complete without refresh (AC-FR*)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(),
    )
    called: list[UUID] = []

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.error_code is None
    assert final.metrics == {
        "freshness_outcome": "skipped_kill_switch",
        "documents_processed": 0,
    }
    assert called == []


def test_freshness_worker_records_run_history_on_kill_switch_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-289/TC-290: kill-switch skip persists a blocked automation_runs row."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(),
    )
    recorded: list[dict[str, object]] = []

    class _RecordingWriteClient(_StubWriteClient):
        def record_automation_run(self, **kwargs: object) -> None:
            recorded.append(dict(kwargs))

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        perform_refresh=lambda _doc: None,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "freshness_outcome": "skipped_kill_switch",
        "documents_processed": 0,
    }
    assert recorded == [
        {
            "job_type": "freshness_refresh",
            "status": "blocked",
            "document_id": DOC_ID,
            "revision": None,
            "error": None,
        }
    ]


def test_freshness_worker_disabled_skips_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VECINITA_FRESHNESS_ENABLED=false → skip scheduled refresh."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(force=False),
    )
    called: list[UUID] = []

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "freshness_outcome": "skipped_disabled",
        "documents_processed": 0,
    }
    assert called == []


def test_freshness_worker_refresh_disabled_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-259: per-source refresh_enabled=false → skip."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(refresh_enabled=False, is_stale=True),
    )
    called: list[UUID] = []

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "freshness_outcome": "skipped_refresh_disabled",
        "documents_processed": 0,
    }
    assert called == []


def test_freshness_worker_not_stale_skips_unless_force(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scheduled non-stale skips; force (Refresh now) still runs (TC-259)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    skipped = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(force=False, is_stale=False),
    )
    forced = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(force=True, is_stale=False),
    )
    called: list[UUID] = []

    run_freshness_refresh_job(
        skipped.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )
    run_freshness_refresh_job(
        forced.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )

    skip_final = store.get_job(skipped.job_id)
    force_final = store.get_job(forced.job_id)
    assert skip_final is not None
    assert force_final is not None
    assert skip_final.metrics == {
        "freshness_outcome": "skipped_not_stale",
        "documents_processed": 0,
    }
    assert force_final.metrics == {
        "freshness_outcome": "refreshed",
        "documents_processed": 1,
    }
    assert called == [DOC_ID]


def test_freshness_worker_stale_calls_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-256: stale + enabled → perform refresh once."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(is_stale=True),
    )
    called: list[UUID] = []

    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.error_code is None
    assert final.metrics == {
        "freshness_outcome": "refreshed",
        "documents_processed": 1,
    }
    assert called == [DOC_ID]


def test_run_job_dispatches_freshness_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_job routes job_type=freshness_refresh to the freshness worker."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(),
    )
    dispatched: list[UUID] = []

    def _fake_freshness(job_id: UUID, **kwargs: object) -> None:
        store_obj = kwargs["store"]
        assert isinstance(store_obj, InMemoryJobStore)
        dispatched.append(job_id)
        _ = store_obj.update_job(
            job_id,
            status="completed",
            metrics={"freshness_outcome": "refreshed", "documents_processed": 1},
        )

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_freshness_refresh_job",
        _fake_freshness,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert dispatched == [record.job_id]
    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"


def test_create_job_request_accepts_freshness_refresh() -> None:
    """POST /jobs schema accepts job_type=freshness_refresh with document_id."""
    body = CreateJobRequest.model_validate(
        {
            "urls": [],
            "options": {
                "job_type": "freshness_refresh",
                "document_id": str(DOC_ID),
                "force": True,
            },
        }
    )
    assert body.options is not None
    assert body.options.job_type == "freshness_refresh"
    assert body.options.document_id == DOC_ID
    assert body.options.force is True


def test_scheduled_freshness_tick_enqueues_stale_enabled_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TP2 / TC-264: schedule branch enqueues freshness_refresh for stale docs."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    enqueued: list[tuple[UUID, bool]] = []

    def list_stale() -> list[DocumentSummary]:
        return [
            DocumentSummary(
                document_id=DOC_ID,
                url="https://example.com/a",
                refresh_enabled=True,
                last_checked_at=_NOW - timedelta(days=31),
                stale=True,
            ),
            DocumentSummary(
                document_id=DOC_ID_2,
                url="https://example.com/b",
                refresh_enabled=False,
                last_checked_at=_NOW - timedelta(days=40),
                stale=True,
            ),
        ]

    def enqueue(document_id: UUID, *, force: bool = False) -> UUID:
        enqueued.append((document_id, force))
        return document_id

    result = run_scheduled_freshness_tick(
        list_stale_documents=list_stale,
        enqueue_freshness=enqueue,
    )

    assert enqueued == [(DOC_ID, False)]
    assert result == {
        "job_type": "freshness_refresh",
        "enqueued": 1,
        "skipped": 1,
        "outcome": "enqueued",
    }


def test_scheduled_freshness_tick_respects_kill_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kill-switch → schedule freshness branch no-ops (AC-FR5 infra only)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    called = False

    def list_stale() -> list[DocumentSummary]:
        nonlocal called
        called = True
        return []

    def enqueue_unused(document_id: UUID, *, force: bool = False) -> UUID:
        _ = (document_id, force)
        return DOC_ID

    result = run_scheduled_freshness_tick(
        list_stale_documents=list_stale,
        enqueue_freshness=enqueue_unused,
    )
    assert called is False
    assert result == {
        "job_type": "freshness_refresh",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "skipped_kill_switch",
    }


def test_scheduled_freshness_tick_respects_master_disable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Master freshness disable → schedule branch skips listing/enqueue."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")

    def enqueue_unused(document_id: UUID, *, force: bool = False) -> UUID:
        _ = (document_id, force)
        return DOC_ID

    result = run_scheduled_freshness_tick(
        list_stale_documents=lambda: [
            DocumentSummary(
                document_id=DOC_ID,
                url="https://example.com/a",
                refresh_enabled=True,
                stale=True,
            )
        ],
        enqueue_freshness=enqueue_unused,
    )
    assert result["outcome"] == "skipped_disabled"
    assert result["enqueued"] == 0


def test_freshness_schedule_does_not_call_catchup_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-FR5 / TC-264: freshness schedule must not enqueue automation_catchup."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    catchup_calls: list[object] = []

    def enqueue_freshness(
        document_id: UUID,
        *,
        force: bool = False,
    ) -> UUID:
        _ = force
        return document_id

    def enqueue_catchup(*_args: object, **_kwargs: object) -> UUID:
        catchup_calls.append((_args, _kwargs))
        return DOC_ID

    _ = enqueue_catchup  # available for accidental wiring; must stay unused
    result = run_scheduled_freshness_tick(
        list_stale_documents=lambda: [
            DocumentSummary(
                document_id=DOC_ID,
                url="https://example.com/a",
                refresh_enabled=True,
                stale=True,
            )
        ],
        enqueue_freshness=enqueue_freshness,
    )
    assert result["enqueued"] == 1
    assert catchup_calls == []


def test_data_management_app_freshness_tick_not_stub() -> None:
    """T128.4: Modal schedule freshness branch is real (not M128 stub)."""
    path = Path(__file__).resolve().parents[3] / "infra" / "modal" / "data_management_app.py"
    source = path.read_text(encoding="utf-8")
    assert "freshness_refresh_stub" not in source
    assert "run_scheduled_freshness_tick" in source
    assert "enqueue_freshness_refresh" in source


def test_freshness_worker_failure_marks_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh errors fail the job with error_code (not silent skip)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(),
    )

    def _boom(_document_id: UUID) -> None:
        msg = "fetch failed"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="fetch failed"):
        run_freshness_refresh_job(
            record.job_id,
            store=store,
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            perform_refresh=_boom,
        )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "failed"
    assert final.error_code == "RuntimeError"
    assert final.metrics == {
        "freshness_outcome": "failed",
        "documents_processed": 0,
    }


def test_freshness_worker_default_requires_embed_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hash-aware default path requires embed_client (T128.5)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options=_freshness_options(force=True, is_stale=False),
    )

    class _Write(_StubWriteClient):
        def get_document_detail(self, document_id: UUID) -> object:
            _ = document_id
            return object()

    with pytest.raises(RuntimeError, match="embed_client is required"):
        run_freshness_refresh_job(
            record.job_id,
            store=store,
            write_client=_Write(),  # type: ignore[arg-type]
        )
    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "failed"
    assert final.error_code == "RuntimeError"
    assert final.metrics == {
        "freshness_outcome": "failed",
        "documents_processed": 0,
    }


def test_freshness_worker_rejects_wrong_job_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-freshness job_type raises ValueError."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com"], job_type="ingest")
    with pytest.raises(ValueError, match="not a freshness_refresh"):
        run_freshness_refresh_job(
            record.job_id,
            store=store,
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            perform_refresh=lambda _doc: None,
        )


def test_freshness_worker_missing_job_raises_key_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown job_id raises KeyError."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_freshness_refresh_job(
            DOC_ID,
            store=store,
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            perform_refresh=lambda _doc: None,
        )


def test_freshness_worker_requires_document_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing document_id in options raises ValueError."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options={"force": True, "refresh_enabled": True, "is_stale": True},
    )
    with pytest.raises(ValueError, match="document_id required"):
        run_freshness_refresh_job(
            record.job_id,
            store=store,
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            perform_refresh=lambda _doc: None,
        )


def test_freshness_worker_parses_string_bool_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """String bool option values are accepted for force / refresh_enabled / is_stale."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options={
            "document_id": str(DOC_ID),
            "force": "true",
            "refresh_enabled": "yes",
            "is_stale": "0",
        },
    )
    called: list[UUID] = []
    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )
    assert called == [DOC_ID]


def test_freshness_worker_option_defaults_and_int_bool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing option keys use defaults; non-str/non-bool values use bool()."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options={"document_id": str(DOC_ID), "force": 1},
    )
    called: list[UUID] = []
    run_freshness_refresh_job(
        record.job_id,
        store=store,
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_refresh=called.append,
    )
    assert called == [DOC_ID]


def test_scheduled_freshness_tick_noop_when_no_stale_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Enabled schedule with empty stale list returns noop."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")

    def enqueue_unused(document_id: UUID, *, force: bool = False) -> UUID:
        _ = (document_id, force)
        return DOC_ID

    result = run_scheduled_freshness_tick(
        list_stale_documents=list,
        enqueue_freshness=enqueue_unused,
    )
    assert result == {
        "job_type": "freshness_refresh",
        "enqueued": 0,
        "skipped": 0,
        "outcome": "noop",
    }


def test_create_job_request_stores_freshness_option_flags() -> None:
    """JobOptions refresh_enabled / is_stale round-trip on CreateJobRequest."""
    body = CreateJobRequest.model_validate(
        {
            "urls": [],
            "options": {
                "job_type": "freshness_refresh",
                "document_id": str(DOC_ID),
                "force": False,
                "refresh_enabled": False,
                "is_stale": True,
            },
        }
    )
    assert body.options is not None
    assert body.options.refresh_enabled is False
    assert body.options.is_stale is True

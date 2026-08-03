"""Unit tests for vecinita_data_management_backend.jobs."""

from __future__ import annotations

from typing import Never
from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.jobs import (
    run_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore


class _StubEmbedClient:
    """StubEmbedClient."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [[0.0] * 384 for _ in texts]


class _StubWriteClient:
    """StubWriteClient."""

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _StubWriteClient:
        """Return self — audit actor scoping is a no-op in unit stubs."""
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        """No-op audit emit for unit stubs."""
        _ = event

    def upsert_batch(self, body: object) -> None:
        """Upsert batch."""
        _ = body


class _StubTagClient:
    """StubTagClient."""

    def infer_document_tags(
        self,
        *,
        title: str,
        text: str,
        language: str,
        vocabulary: list[str],
        max_tags: int = 10,
    ) -> list[str]:
        """Infer document tags."""
        _ = (title, text, language, max_tags)
        return [vocabulary[0]] if vocabulary else []


def test_run_job_raises_when_job_missing() -> None:
    """Test run job raises when job missing."""
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        run_job(
            uuid4(),
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )


def test_run_job_retag_requires_tag_client() -> None:
    """Test run job retag requires tag client."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="retag", options={"document_id": str(uuid4())})

    with pytest.raises(RuntimeError, match="tag_client"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            tag_client=None,
        )


def test_run_job_dispatches_backfill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backfill flag routes to run_backfill_job (T87.5 / TP-S017-08)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rescrape", "backfill": True, "backfill_source": "rescrape"},
    )
    called: list[UUID] = []

    def _backfill(job_id: UUID, **kwargs: object) -> None:
        _ = kwargs
        called.append(job_id)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_backfill_job",
        _backfill,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert called == [record.job_id]


def test_run_job_dispatches_rebuild(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """job_type=rebuild routes to run_rebuild_job (T88.3 / ADR-040)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rechunk", "force": True},
    )
    called: list[UUID] = []

    def _rebuild(job_id: UUID, **kwargs: object) -> None:
        _ = kwargs
        called.append(job_id)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_rebuild_job",
        _rebuild,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert called == [record.job_id]


def test_run_job_dispatches_eval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """job_type=eval routes to run_eval_job (BUG-2026-07-31 / ADR-038)."""
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id)},
    )
    called: list[UUID] = []

    def _eval(job_id: UUID, **kwargs: object) -> None:
        _ = kwargs
        called.append(job_id)
        store.update_job(job_id, status="completed")

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_eval_job",
        _eval,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert called == [record.job_id]


def test_run_job_dispatches_retag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run job dispatches retag."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="retag", options={"document_id": str(uuid4())})
    called: list[UUID] = []

    def _retag(job_id: UUID, **kwargs: object) -> None:
        """Retag."""
        called.append(job_id)
        assert kwargs["tag_client"] is not None

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_retag_job",
        _retag,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        tag_client=_StubTagClient(),  # type: ignore[arg-type]
    )

    assert called == [record.job_id]


def test_run_job_dispatches_ingest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run job dispatches ingest."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    called: list[UUID] = []

    def _ingest(job_id: UUID, **kwargs: object) -> None:
        """Ingest."""
        _ = kwargs
        called.append(job_id)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_ingest_job",
        _ingest,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type],
    )

    assert called == [record.job_id]


def test_run_job_skips_failure_update_when_job_already_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run job skips failure update when job already terminal."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    store.update_job(record.job_id, status="completed")

    def _fail(_job_id: UUID, **_kwargs: object) -> Never:
        """Fail."""
        msg = "late failure"
        raise ValueError(msg)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_ingest_job",
        _fail,
    )

    with pytest.raises(ValueError, match="late failure"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_job_marks_failed_when_pipeline_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run job marks failed when pipeline raises."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])

    def _fail(_job_id: UUID, **_kwargs: object) -> Never:
        """Fail."""
        msg = "pipeline exploded"
        raise ValueError(msg)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_ingest_job",
        _fail,
    )

    with pytest.raises(ValueError, match="pipeline exploded"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "ValueError"


def test_run_job_rejects_unknown_job_type() -> None:
    """Unknown job_type raises ValueError from the dispatcher."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"], job_type="ingest")
    store.update_job(record.job_id, status="queued")
    # Bypass create_job validation by mutating the in-memory record.
    mutated = store.get_job(record.job_id)
    assert mutated is not None
    mutated.job_type = "not-a-real-type"

    with pytest.raises(ValueError, match="unknown job_type"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )


def test_run_job_audit_emit_failure_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audit emit exceptions must not fail a successful job."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])

    def _ok(_job_id: UUID, **_kwargs: object) -> None:
        store.update_job(_job_id, status="completed")

    class _AuditFailWrite(_StubWriteClient):
        def post_audit_event(self, event: object) -> None:
            _ = event
            msg = "audit down"
            raise RuntimeError(msg)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_ingest_job",
        _ok,
    )
    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_AuditFailWrite(),  # type: ignore[arg-type]
    )
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_job_emits_failed_audit_when_pipeline_already_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the pipeline already marked failed, run_job audits without re-updating."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    events: list[str] = []

    def _fail_marked(_job_id: UUID, **_kwargs: object) -> Never:
        store.update_job(
            _job_id,
            status="failed",
            error_code="Boom",
            error_message="already failed",
        )
        msg = "already failed"
        raise RuntimeError(msg)

    class _AuditWrite(_StubWriteClient):
        def post_audit_event(self, event: object) -> None:
            payload = getattr(event, "event_type", None)
            events.append(str(payload))

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_ingest_job",
        _fail_marked,
    )
    with pytest.raises(RuntimeError, match="already failed"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_AuditWrite(),  # type: ignore[arg-type]
        )
    assert "job.failed" in events

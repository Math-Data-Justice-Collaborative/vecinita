"""Unit tests for vecinita_data_management_backend.jobs."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


class _StubWriteClient:
    def upsert_batch(self, body: object) -> None:
        _ = body


class _StubTagClient:
    def infer_document_tags(
        self,
        *,
        title: str,
        text: str,
        language: str,
        vocabulary: list[str],
        max_tags: int = 10,
    ) -> list[str]:
        _ = (title, text, language, max_tags)
        return [vocabulary[0]] if vocabulary else []


def test_run_job_raises_when_job_missing() -> None:
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        run_job(
            uuid4(),
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )


def test_run_job_retag_requires_tag_client() -> None:
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


def test_run_job_dispatches_retag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="retag", options={"document_id": str(uuid4())})
    called: list[UUID] = []

    def _retag(job_id, **kwargs):  # type: ignore[no-untyped-def]
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
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    called: list[UUID] = []

    def _ingest(job_id, **kwargs):  # type: ignore[no-untyped-def]
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
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])
    store.update_job(record.job_id, status="completed")

    def _fail(_job_id, **_kwargs):  # type: ignore[no-untyped-def]
        raise ValueError("late failure")

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
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])

    def _fail(_job_id, **_kwargs):  # type: ignore[no-untyped-def]
        raise ValueError("pipeline exploded")

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

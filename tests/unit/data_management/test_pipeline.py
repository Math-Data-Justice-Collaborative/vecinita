"""Unit tests for vecinita_data_management_backend.pipeline."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from vecinita_data_management_backend.pipeline import (
    fetch_html_fixture,
    run_ingest_job,
    run_retag_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, DocumentDetail, TagInput
from vecinita_tagging.vocabulary import SeedTag

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
    SeedTag(slug="legal", label_en="Legal", label_es="Legal"),
]


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.last_batch: BatchUpsertRequest | None = None
        self.patched_tags: list[TagInput] | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        self.last_batch = body

    def get_document_detail(self, document_id):  # type: ignore[no-untyped-def]
        return DocumentDetail(
            document_id=document_id,
            title="Tenant rights",
            text="Information about housing rights and legal aid.",
            language="en",
            url="https://example.com/doc",
        )

    def patch_document_tags(self, document_id, tags: list[TagInput]):  # type: ignore[no-untyped-def]
        _ = document_id
        self.patched_tags = tags
        from vecinita_shared_schemas.internal_write import TagPatchResponse

        return TagPatchResponse(tags=tags)


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
        return ["housing"] if "housing" in vocabulary else []


def _fetch_fixture(url: str) -> ScrapedDocument:
    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


def test_fetch_html_fixture_parses_fixture() -> None:
    doc = fetch_html_fixture("fixture://sample", fixture_html=_FIXTURE_HTML)

    assert doc.title == "Sample public notice"
    assert "Neighborhood clinic" in doc.text


def test_run_ingest_job_completes_with_fixture_html() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/sample-page.html"],
        options={"chunk_size_tokens": "64"},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch_fixture,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert write_client.last_batch is not None
    assert write_client.last_batch.documents[0].language in {"en", "es"}


def test_run_ingest_job_applies_llm_tags_when_client_provided() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(urls=["https://example.com/sample-page.html"])

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch_fixture,
        tag_client=_StubTagClient(),  # type: ignore[arg-type]
        tag_vocabulary=_VOCAB,
    )

    assert write_client.last_batch is not None
    tags = write_client.last_batch.documents[0].tags
    assert tags is not None
    assert tags[0].slug == "housing"


def test_run_ingest_job_raises_when_job_missing() -> None:
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        run_ingest_job(
            uuid4(),
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            fetch_document=_fetch_fixture,
        )


def test_run_ingest_job_marks_failed_when_no_chunks() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(urls=["https://example.com/blank"])

    def blank(url: str) -> ScrapedDocument:
        return ScrapedDocument(url=url, title=None, text="   ")

    with pytest.raises(ValueError, match="no chunks"):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
            fetch_document=blank,
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


def test_run_retag_job_completes() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    document_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(document_id)},
    )

    run_retag_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
        tag_client=_StubTagClient(),  # type: ignore[arg-type]
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert write_client.patched_tags is not None
    assert write_client.patched_tags[0].slug == "housing"


def test_run_retag_job_detects_language_when_missing() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    document_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(document_id)},
    )

    def _detail(doc_id):  # type: ignore[no-untyped-def]
        return DocumentDetail(
            document_id=doc_id,
            title="Aviso",
            text="Este documento explica los derechos de los inquilinos en español.",
            language=None,
            url="https://example.com/es-doc",
        )

    write_client.get_document_detail = _detail  # type: ignore[method-assign]

    run_retag_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
        tag_client=_StubTagClient(),  # type: ignore[arg-type]
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_retag_job_raises_when_job_missing() -> None:
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        run_retag_job(
            uuid4(),
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
        )


def test_run_retag_job_marks_failed_on_write_error() -> None:
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    document_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(document_id)},
    )

    def _boom(_document_id, _tags):  # type: ignore[no-untyped-def]
        raise RuntimeError("write unavailable")

    write_client.patch_document_tags = _boom  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="write unavailable"):
        run_retag_job(
            record.job_id,
            store=store,
            write_client=write_client,  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
            tag_vocabulary=_VOCAB,
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


def test_run_retag_job_rejects_non_retag_job() -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/page"])

    with pytest.raises(ValueError, match="not a retag job"):
        run_retag_job(
            record.job_id,
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
        )


def test_run_retag_job_requires_document_id_option() -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="retag", options={})

    with pytest.raises(ValueError, match="document_id"):
        run_retag_job(
            record.job_id,
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
        )

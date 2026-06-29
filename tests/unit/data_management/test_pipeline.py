"""Unit tests for vecinita_data_management_backend.pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Never
from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.pipeline import (
    fetch_html_fixture,
    run_ingest_job,
    run_retag_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    DocumentDetail,
    TagInput,
    TagPatchResponse,
)
from vecinita_tagging.vocabulary import SeedTag

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
    SeedTag(slug="legal", label_en="Legal", label_es="Legal"),
]


class _StubEmbedClient:
    """StubEmbedClient."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [[0.01] * 384 for _ in texts]


class _RecordingWriteClient:
    """RecordingWriteClient."""

    def __init__(self) -> None:
        """Init  ."""
        self.last_batch: BatchUpsertRequest | None = None
        self.patched_tags: list[TagInput] | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        """Upsert batch."""
        self.last_batch = body

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        """Get document detail."""
        return DocumentDetail(
            document_id=document_id,
            title="Tenant rights",
            text="Information about housing rights and legal aid.",
            language="en",
            url="https://example.com/doc",
        )

    def patch_document_tags(
        self,
        document_id: UUID,
        tags: list[TagInput],
    ) -> TagPatchResponse:
        """Patch document tags."""
        _ = document_id
        self.patched_tags = tags
        return TagPatchResponse(tags=tags)


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
        return ["housing"] if "housing" in vocabulary else []


def _fetch_fixture(url: str) -> ScrapedDocument:
    """Fetch fixture."""
    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


def test_fetch_html_fixture_parses_fixture() -> None:
    """Test fetch html fixture parses fixture."""
    doc = fetch_html_fixture("fixture://sample", fixture_html=_FIXTURE_HTML)

    assert doc.title == "Sample public notice"
    assert "Neighborhood clinic" in doc.text


def test_run_ingest_job_completes_with_fixture_html() -> None:
    """Test run ingest job completes with fixture html."""
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
    """Test run ingest job applies llm tags when client provided."""
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
    """Test run ingest job raises when job missing."""
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
    """Test run ingest job marks failed when no chunks."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(urls=["https://example.com/blank"])

    def blank(url: str) -> ScrapedDocument:
        """Blank."""
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
    """Test run retag job completes."""
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
    """Test run retag job detects language when missing."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    document_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(document_id)},
    )

    def _detail(doc_id: UUID) -> DocumentDetail:
        """Detail."""
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
    """Test run retag job raises when job missing."""
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        run_retag_job(
            uuid4(),
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
        )


def test_run_retag_job_marks_failed_on_write_error() -> None:
    """Test run retag job marks failed on write error."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    document_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(document_id)},
    )

    def _boom(_document_id: UUID, _tags: list[TagInput]) -> Never:
        """Boom."""
        msg = "write unavailable"
        raise RuntimeError(msg)

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
    """Test run retag job rejects non retag job."""
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
    """Test run retag job requires document id option."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="retag", options={})

    with pytest.raises(ValueError, match="document_id"):
        run_retag_job(
            record.job_id,
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
            tag_client=_StubTagClient(),  # type: ignore[arg-type]
        )

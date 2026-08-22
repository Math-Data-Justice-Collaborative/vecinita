"""Pipeline tests for F75 ingest bilingual translation (TC-252)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from vecinita_data_management_backend.pipeline import (
    _build_translation_documents,
    _translate_locales_from_options,
    fetch_html_fixture,
    run_ingest_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.internal_write import (
    BatchUpsertDocumentResult,
    BatchUpsertRequest,
    BatchUpsertResponse,
    ChunkUpsert,
    DocumentUpsert,
)
from vecinita_tagging.vocabulary import SeedTag

if TYPE_CHECKING:
    from vecinita_ingest.models import ScrapedDocument

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_SOURCE_ID = UUID("11111111-1111-4111-8111-111111111111")
_EXPECTED_UPSERT_BATCHES_WITH_TRANSLATION = 2
_VOCAB = [SeedTag(slug="housing", label_en="Housing", label_es="Vivienda")]


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.02] * 384 for _ in texts]


class _StubTranslateClient:
    def translate_chunk(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        _ = source_locale
        return f"[{target_locale}] {text}"


class _FailingTranslateClient:
    def translate_chunk(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        _ = (text, source_locale, target_locale)
        msg = "mt unavailable"
        raise RuntimeError(msg)


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.batches: list[BatchUpsertRequest] = []

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        self.batches.append(body)
        if len(self.batches) == 1:
            doc = body.documents[0]
            return BatchUpsertResponse(
                upserted_chunks=len(doc.chunks),
                documents=[
                    BatchUpsertDocumentResult(
                        document_id=_SOURCE_ID,
                        url=str(doc.url),
                        language=doc.language,
                    )
                ],
            )
        translated = body.documents[0]
        return BatchUpsertResponse(
            upserted_chunks=len(translated.chunks),
            documents=[
                BatchUpsertDocumentResult(
                    document_id=uuid4(),
                    url=str(translated.url),
                    language=translated.language,
                )
            ],
        )

    def get_content_hash_by_url(self, url: str) -> str | None:
        _ = url
        return None


def _fetch_fixture(url: str) -> ScrapedDocument:

    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


def test_run_ingest_job_with_translate_locales_writes_draft_pair() -> None:
    """TC-252: translate_locales creates draft ES sibling linked to source."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/sample-page.html"],
        options={"chunk_size_tokens": "64", "translate_locales": ["es"]},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch_fixture,
        translate_client=_StubTranslateClient(),
        tag_vocabulary=_VOCAB,
    )

    assert len(write_client.batches) == _EXPECTED_UPSERT_BATCHES_WITH_TRANSLATION
    source = write_client.batches[0].documents[0]
    translated = write_client.batches[1].documents[0]
    assert source.language in {"en", "es"}
    assert translated.language == "es"
    assert translated.paired_document_id == _SOURCE_ID
    assert translated.publish_status == "draft"
    assert translated.chunks[0].text.startswith("[es] ")

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.metrics is not None
    assert updated.metrics["translated_documents"] == 1
    assert updated.metrics["translated_chunks"] == len(translated.chunks)


def test_run_ingest_job_without_translate_locales_unchanged() -> None:
    """Default ingest does not call translation path."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(urls=["https://example.com/sample-page.html"])

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch_fixture,
        tag_vocabulary=_VOCAB,
    )

    assert len(write_client.batches) == 1


def test_translate_locales_from_options_parses_deduped_locales() -> None:
    """Invalid entries are ignored; en/es are deduped."""
    assert _translate_locales_from_options({"translate_locales": ["es", "es", "fr", "en"]}) == [
        "es",
        "en",
    ]
    assert _translate_locales_from_options({"translate_locales": "es"}) == []
    assert _translate_locales_from_options({}) == []


def test_build_translation_documents_skips_same_language_target() -> None:
    """Requesting translation to the source locale increments skipped, not documents."""
    source = DocumentUpsert(
        url="https://example.com/page",
        title="Title",
        language="en",
        chunks=[ChunkUpsert(chunk_index=0, text="hello", embedding=[0.1] * 384)],
    )
    docs, stats = _build_translation_documents(
        source_documents=[source],
        upserted=BatchUpsertResponse(
            upserted_chunks=1,
            documents=[
                BatchUpsertDocumentResult(
                    document_id=_SOURCE_ID,
                    url="https://example.com/page",
                    language="en",
                )
            ],
        ),
        translate_locales=["en"],
        translate_client=_StubTranslateClient(),
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        chunk_size=64,
    )
    assert docs == []
    assert stats == {"documents": 0, "chunks": 0, "skipped": 1, "failed": 0}


def test_build_translation_documents_soft_fails_on_translate_error() -> None:
    """MT errors increment failed without raising."""
    source = DocumentUpsert(
        url="https://example.com/page",
        title="Title",
        language="en",
        chunks=[ChunkUpsert(chunk_index=0, text="hello", embedding=[0.1] * 384)],
    )
    docs, stats = _build_translation_documents(
        source_documents=[source],
        upserted=BatchUpsertResponse(
            upserted_chunks=1,
            documents=[
                BatchUpsertDocumentResult(
                    document_id=_SOURCE_ID,
                    url="https://example.com/page",
                    language="en",
                )
            ],
        ),
        translate_locales=["es"],
        translate_client=_FailingTranslateClient(),
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        chunk_size=64,
    )
    assert docs == []
    assert stats == {"documents": 0, "chunks": 0, "skipped": 0, "failed": 1}


def test_run_ingest_job_translate_locales_without_client_records_zero_metrics() -> None:
    """translate_locales set but no client leaves metrics at zero translated counts."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/sample-page.html"],
        options={"chunk_size_tokens": "64", "translate_locales": ["es"]},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch_fixture,
        tag_vocabulary=_VOCAB,
    )

    assert len(write_client.batches) == 1
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.metrics is not None
    assert updated.metrics["translated_documents"] == 0
    assert updated.metrics["translation_failed"] == 0

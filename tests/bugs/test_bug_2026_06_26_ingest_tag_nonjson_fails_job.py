"""Regression test for BUG-2026-06-26 — ingest job fails on non-JSON LLM tag response (#88).

A tag-inference failure (empty / non-JSON completion from vecinita-llm) must NOT fail the
whole ingest job. Tagging is best-effort enrichment; the document, chunks, and embeddings
are still ingestable without LLM tags.
"""

from __future__ import annotations

from pathlib import Path

from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import BatchUpsertRequest
from vecinita_tagging.llm_client import LlmTagClientError
from vecinita_tagging.vocabulary import SeedTag

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
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

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        self.last_batch = body


class _NonJsonTagClient:
    """Mimics vecinita-llm returning an empty / non-JSON tag completion."""

    def infer_document_tags(
        self,
        *,
        title: str,
        text: str,
        language: str,
        vocabulary: list[str],
        max_tags: int = 10,
    ) -> list[str]:
        _ = (title, text, language, vocabulary, max_tags)
        raise LlmTagClientError(
            "tag response is not valid JSON: Expecting value: line 1 column 1 (char 0)"
        )


def _fetch_fixture(url: str) -> ScrapedDocument:
    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


def test_ingest_job_completes_when_tag_inference_returns_non_json() -> None:
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
        tag_client=_NonJsonTagClient(),  # type: ignore[arg-type]
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert write_client.last_batch is not None
    doc = write_client.last_batch.documents[0]
    assert doc.tags is None or doc.tags == []

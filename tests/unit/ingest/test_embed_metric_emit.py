"""F84: ingest embed stage fires privacy-safe metrics events (ADR-055)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EmbeddingClientError
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentDetail,
    TagInput,
    TagPatchResponse,
)
from vecinita_tagging.vocabulary import SeedTag

if TYPE_CHECKING:
    from collections.abc import Mapping
    from uuid import UUID

    from vecinita_ingest.models import ScrapedDocument

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
]


class _StubEmbed:
    """Successful embed client."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]


class _FailEmbed:
    """Embed client that always fails."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        _ = texts
        msg = "modal embed 503"
        raise EmbeddingClientError(msg)


class _WriteClient:
    """Write client that records metrics events."""

    def __init__(self) -> None:
        self.metric_events: list[Mapping[str, object]] = []
        self.last_batch: BatchUpsertRequest | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        self.last_batch = body
        n_chunks = sum(len(doc.chunks) for doc in body.documents)
        return BatchUpsertResponse(upserted_chunks=n_chunks)

    def post_metrics_event(  # noqa: PLR0913  # mirrors MetricsEventRequest fields
        self,
        *,
        workload: str,
        outcome: str,
        latency_ms: int,
        error_code: str | None = None,
        job_id: str | None = None,
        locale: str | None = None,
    ) -> None:
        self.metric_events.append(
            {
                "workload": workload,
                "outcome": outcome,
                "latency_ms": latency_ms,
                "error_code": error_code,
                "job_id": job_id,
                "locale": locale,
            }
        )

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        return DocumentDetail(
            document_id=document_id,
            title="t",
            text="x",
            language="en",
            url="https://example.com/doc",
        )

    def patch_document_tags(
        self,
        document_id: UUID,
        tags: list[TagInput],
    ) -> TagPatchResponse:
        _ = (document_id, tags)
        return TagPatchResponse(document_id=document_id, tags=[])


def _fetch(url: str) -> ScrapedDocument:
    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


def test_run_ingest_job_fires_embed_success_metric() -> None:
    """After successful embed, POST allow-listed embed metric with job_id."""
    store = InMemoryJobStore()
    write = _WriteClient()
    record = store.create_job(
        urls=["https://example.com/sample.html"],
        options={"chunk_size_tokens": "64"},
    )
    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbed(),  # type: ignore[arg-type]
        write_client=write,  # type: ignore[arg-type]
        fetch_document=_fetch,
        tag_vocabulary=_VOCAB,
    )
    assert len(write.metric_events) >= 1
    event = write.metric_events[0]
    assert event["workload"] == "embed"
    assert event["outcome"] == "success"
    assert event["job_id"] == str(record.job_id)
    assert isinstance(event["latency_ms"], int)
    assert event["latency_ms"] >= 0
    assert "question" not in event
    assert "answer" not in event
    assert "text" not in event


def test_run_ingest_job_fires_embed_failure_metric() -> None:
    """EmbedClientError records failure metric with error_code and job_id."""
    store = InMemoryJobStore()
    write = _WriteClient()
    record = store.create_job(
        urls=["https://example.com/sample.html"],
        options={"chunk_size_tokens": "64"},
    )
    with pytest.raises(EmbeddingClientError):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_FailEmbed(),  # type: ignore[arg-type]
            write_client=write,  # type: ignore[arg-type]
            fetch_document=_fetch,
            tag_vocabulary=_VOCAB,
        )
    assert len(write.metric_events) == 1
    event = write.metric_events[0]
    assert event["workload"] == "embed"
    assert event["outcome"] == "failure"
    assert event["error_code"] == "EmbeddingClientError"
    assert event["job_id"] == str(record.job_id)
    assert isinstance(event["latency_ms"], int)
    assert event["locale"] is None

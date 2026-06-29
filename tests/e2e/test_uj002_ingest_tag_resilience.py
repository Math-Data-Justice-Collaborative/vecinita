"""E2E regression for #88 (BUG-2026-06-26): a non-JSON LLM tag completion must not fail ingest.

Tagging is best-effort enrichment (F20). When `vecinita-llm` returns an empty / non-JSON
completion, `run_ingest_job` raises `LlmTagClientError` internally but the document, chunks,
and embeddings are still ingestable, so the job must reach `completed` (not `failed`) and the
document is written with no LLM tags. This exercises the full data-management ASGI app
(`POST /jobs` -> background runner -> `GET /jobs/{id}` -> `GET /jobs`), the level at which
the original regression surfaced (job `failed` in staging).
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, BatchUpsertResponse
from vecinita_tagging.llm_client import LlmTagClientError
from vecinita_tagging.vocabulary import SeedTag

from tests.helpers.json_response import json_object_list, json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

pytestmark = pytest.mark.e2e

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
    SeedTag(slug="legal", label_en="Legal", label_es="Legal"),
]


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        """Close."""
        return


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.last_batch: BatchUpsertRequest | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """Upsert batch."""
        self.last_batch = body
        chunks = sum(len(doc.chunks) for doc in body.documents)
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        """Close."""
        return


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
        """Infer document tags."""
        _ = (title, text, language, vocabulary, max_tags)
        msg = "tag response is not valid JSON: Expecting value: line 1 column 1 (char 0)"
        raise LlmTagClientError(msg)


@pytest.fixture
def resilient_dm_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, _RecordingWriteClient]:
    """Resilient dm client."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()

    def runner(job_id: UUID) -> None:
        """Runner."""
        run_ingest_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
            fetch_document=lambda url: fetch_html_fixture(url, fixture_html=_FIXTURE_HTML),
            tag_client=_NonJsonTagClient(),  # type: ignore[arg-type]
            tag_vocabulary=_VOCAB,
        )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client, write_client


def test_ingest_completes_when_llm_tag_response_is_non_json(
    resilient_dm_client: tuple[TestClient, _RecordingWriteClient],
) -> None:
    """Ingest completes when llm tag response is non json."""
    client, write_client = resilient_dm_client

    create = client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/sample-page.html"],
            "options": {"chunk_size_tokens": 64},
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == HTTPStatus.OK
    body = response_json_object(status)
    # Regression: a transient non-JSON tag completion previously marked the job `failed`.
    assert json_str(body, "status") == "completed"
    assert body["error_code"] is None

    # The document is still written; it just carries no LLM tags.
    assert write_client.last_batch is not None
    document = write_client.last_batch.documents[0]
    assert document.tags is None or document.tags == []

    # And the completed job is observable in the Job Management list (#89), not lost.
    listed = response_json_object(client.get("/jobs"))
    job_ids = {json_str(job, "job_id") for job in json_object_list(listed, "jobs")}
    assert job_id in job_ids

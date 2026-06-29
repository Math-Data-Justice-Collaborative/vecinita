"""E2E tests for ingest pipeline with LLM auto-tagging (TC-047, UJ-002)."""

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

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

pytestmark = pytest.mark.e2e

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_MAX_DOCUMENT_TAGS = 10


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        """Close."""
        return


class _MockWriteClient:
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


class _MockTagClient:
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
        del title, text, language, vocabulary
        return ["housing", "legal"][:max_tags]


@pytest.fixture
def tagged_dm_client() -> tuple[TestClient, _MockWriteClient]:
    """Tagged dm client."""
    store = InMemoryJobStore()
    mock_write = _MockWriteClient()

    def runner(job_id: UUID) -> None:
        """Runner."""
        run_ingest_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=mock_write,  # type: ignore[arg-type]
            fetch_document=lambda url: fetch_html_fixture(url, fixture_html=_FIXTURE_HTML),
            tag_client=_MockTagClient(),
        )

    app = create_app(
        store=store,
        require_proxy_auth=True,
        pipeline_runner=runner,
    )
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client, mock_write


def test_ingest_job_assigns_llm_document_tags(
    tagged_dm_client: tuple[TestClient, _MockWriteClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ingest job assigns llm document tags."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    client, mock_write = tagged_dm_client

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
    assert json_str(response_json_object(status), "status") == "completed"

    assert mock_write.last_batch is not None
    document = mock_write.last_batch.documents[0]  # type: ignore[attr-defined]
    assert document.tags is not None
    assert len(document.tags) <= _MAX_DOCUMENT_TAGS
    assert all(tag.source == "llm" for tag in document.tags)
    slugs = {tag.slug for tag in document.tags}
    assert slugs <= {"housing", "legal"}

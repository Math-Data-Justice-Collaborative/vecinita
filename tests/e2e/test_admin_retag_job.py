"""Admin async retag job lifecycle with mocked LLM (UJ-011 prep, T16.8)."""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app as create_write_app
from pydantic import HttpUrl
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    ChunkUpsert,
    DocumentDetail,
    DocumentUpsert,
    TagInput,
    TagPatchResponse,
)

pytestmark = pytest.mark.e2e

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_PROXY_KEY = "test-proxy-key"
_WRITE_KEY = "test-write-key"


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
        return ["benefits"][:max_tags]


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_EMBEDDING for _ in texts]

    def close(self) -> None:
        return None


class _TestClientWriteClient:
    """Adapt FastAPI TestClient to InternalWriteClient surface for tests."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def upsert_batch(self, body: BatchUpsertRequest) -> object:
        from vecinita_shared_schemas.internal_write import BatchUpsertResponse

        response = self._client.post(
            "/internal/v1/documents/batch",
            json=body.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {_WRITE_KEY}"},
        )
        assert response.status_code == 200, response.text
        return BatchUpsertResponse.model_validate(response.json())

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        response = self._client.get(
            f"/internal/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {_WRITE_KEY}"},
        )
        assert response.status_code == 200, response.text
        return DocumentDetail.model_validate(response.json())

    def patch_document_tags(self, document_id: UUID, tags: list[TagInput]) -> TagPatchResponse:
        response = self._client.patch(
            f"/internal/v1/documents/{document_id}/tags",
            json={"tags": [tag.model_dump(mode="json") for tag in tags], "source": "llm"},
            headers={"Authorization": f"Bearer {_WRITE_KEY}"},
        )
        assert response.status_code == 200, response.text
        return TagPatchResponse.model_validate(response.json())

    def close(self) -> None:
        return None


@pytest.fixture
def retag_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, TestClient, InMemoryJobStore]:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _WRITE_KEY)
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )

    write_api = TestClient(create_write_app())
    write_api.headers.update({"Authorization": f"Bearer {_WRITE_KEY}"})
    write_client = _TestClientWriteClient(write_api)
    write_client.upsert_batch(
        BatchUpsertRequest(
            documents=[
                DocumentUpsert(
                    url=HttpUrl("https://example.com/retag-target"),
                    title="Retag me",
                    language="en",
                    chunks=[
                        ChunkUpsert(
                            chunk_index=0,
                            text="Community benefits overview.",
                            embedding=_EMBEDDING,
                        )
                    ],
                )
            ]
        )
    )

    store = InMemoryJobStore()

    def runner(job_id: UUID) -> None:
        run_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
            tag_client=_MockTagClient(),  # type: ignore[arg-type]
        )

    dm_app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    dm_client = TestClient(dm_app)
    dm_client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})

    class _InlineJobsClient:
        def enqueue_retag(self, document_id: UUID) -> UUID:
            record = store.create_job(
                urls=[],
                options={"document_id": str(document_id)},
                job_type="retag",
            )
            runner(record.job_id)
            return record.job_id

    write_with_jobs = TestClient(create_write_app(jobs_client=_InlineJobsClient()))  # type: ignore[arg-type]
    write_with_jobs.headers.update({"Authorization": f"Bearer {_WRITE_KEY}"})

    return write_with_jobs, dm_client, store


def test_admin_retag_job_lifecycle(
    retag_clients: tuple[TestClient, TestClient, InMemoryJobStore],
) -> None:
    write_client_api, dm_client, _store = retag_clients

    list_resp = write_client_api.get("/internal/v1/documents")
    assert list_resp.status_code == 200
    document_id = list_resp.json()[0]["document_id"]

    retag_resp = write_client_api.post(f"/internal/v1/documents/{document_id}/retag")
    assert retag_resp.status_code == 200
    job_id = retag_resp.json()["job_id"]

    status = dm_client.get(f"/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        slugs = conn.execute(
            text(
                """
                SELECT t.slug
                FROM document_tags dt
                JOIN tags t ON t.id = dt.tag_id
                WHERE dt.document_id = :document_id
                ORDER BY t.slug
                """
            ),
            {"document_id": document_id},
        ).fetchall()

    assert [row[0] for row in slugs] == ["benefits"]

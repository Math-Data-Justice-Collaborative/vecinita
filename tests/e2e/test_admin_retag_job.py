"""Admin async retag job lifecycle with mocked LLM (UJ-011 prep, T16.8)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import create_engine, text
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.audit_headers import (
    AUDIT_ACTOR_ID_HEADER,
    AUDIT_ACTOR_ROLE_HEADER,
)
from vecinita_shared_schemas.internal_write import (
    AuditEventRequest,
    BatchUpsertRequest,
    BatchUpsertResponse,
    ChunkUpsert,
    DocumentDetail,
    DocumentUpsert,
    TagInput,
    TagPatchResponse,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    json_str,
    response_json_list,
    response_json_object,
)

if TYPE_CHECKING:
    from uuid import UUID


pytestmark = pytest.mark.e2e

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_PROXY_KEY = "test-proxy-key"
_WRITE_KEY = "test-write-key"
_RETAG_TARGET_URL = "https://example.com/retag-target"


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
        _ = (title, text, language, vocabulary)
        return ["benefits"][:max_tags]


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [_EMBEDDING for _ in texts]

    def close(self) -> None:
        """Close."""
        return


class _TestClientWriteClient:
    """Adapt FastAPI TestClient to InternalWriteClient surface for tests."""

    def __init__(
        self,
        client: TestClient,
        *,
        audit_actor_id: UUID | None = None,
        audit_actor_role: str | None = None,
    ) -> None:
        self._client = client
        self._audit_actor_id = audit_actor_id
        self._audit_actor_role = audit_actor_role

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _TestClientWriteClient:
        """Return a client that forwards operator attribution on service-key writes."""
        return _TestClientWriteClient(
            self._client,
            audit_actor_id=actor_id,
            audit_actor_role=actor_role,
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {_WRITE_KEY}"}
        if self._audit_actor_id is not None:
            headers[AUDIT_ACTOR_ID_HEADER] = str(self._audit_actor_id)
        if self._audit_actor_role is not None:
            headers[AUDIT_ACTOR_ROLE_HEADER] = self._audit_actor_role
        return headers

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """Upsert batch."""
        response = self._client.post(
            "/internal/v1/documents/batch",
            json=body.model_dump(mode="json"),
            headers=self._headers(),
        )
        assert response.status_code == HTTPStatus.OK, response.text
        return BatchUpsertResponse.model_validate(response.json())

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        """Get document detail."""
        response = self._client.get(
            f"/internal/v1/documents/{document_id}",
            headers=self._headers(),
        )
        assert response.status_code == HTTPStatus.OK, response.text
        return DocumentDetail.model_validate(response.json())

    def patch_document_tags(self, document_id: UUID, tags: list[TagInput]) -> TagPatchResponse:
        """Patch document tags."""
        response = self._client.patch(
            f"/internal/v1/documents/{document_id}/tags",
            json={"tags": [tag.model_dump(mode="json") for tag in tags], "source": "llm"},
            headers=self._headers(),
        )
        assert response.status_code == HTTPStatus.OK, response.text
        return TagPatchResponse.model_validate(response.json())

    def post_audit_event(self, event: AuditEventRequest) -> None:
        """Emit audit event via internal write API."""
        response = self._client.post(
            "/internal/v1/audit/event",
            json=event.model_dump(mode="json"),
            headers=self._headers(),
        )
        assert response.status_code == HTTPStatus.OK, response.text

    def close(self) -> None:
        """Close."""
        return


def _document_id_for_url(client: TestClient, url: str) -> str:
    docs = response_json_list(client.get("/internal/v1/documents"))
    return json_str(find_json_object_by_str(docs, "url", url), "document_id")


@pytest.fixture
def retag_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, TestClient, InMemoryJobStore, str]:
    """Retag clients."""
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
                    url=HttpUrl(_RETAG_TARGET_URL),
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
        """Runner."""
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
            """Enqueue retag."""
            record = store.create_job(
                urls=[],
                options={"document_id": str(document_id)},
                job_type="retag",
            )
            runner(record.job_id)
            return record.job_id

    write_with_jobs = TestClient(create_write_app(jobs_client=_InlineJobsClient()))  # type: ignore[arg-type]
    write_with_jobs.headers.update({"Authorization": f"Bearer {_WRITE_KEY}"})

    document_id = _document_id_for_url(write_with_jobs, _RETAG_TARGET_URL)
    return write_with_jobs, dm_client, store, document_id


def test_admin_retag_job_lifecycle(
    retag_clients: tuple[TestClient, TestClient, InMemoryJobStore, str],
) -> None:
    """Admin retag job lifecycle."""
    write_client_api, dm_client, _store, document_id = retag_clients

    retag_resp = write_client_api.post(f"/internal/v1/documents/{document_id}/retag")
    assert retag_resp.status_code == HTTPStatus.OK
    job_id = json_str(response_json_object(retag_resp), "job_id")

    status = dm_client.get(f"/jobs/{job_id}")
    assert status.status_code == HTTPStatus.OK
    assert json_str(response_json_object(status), "status") == "completed"

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


def test_admin_retag_tags_visible_via_get_endpoint(
    retag_clients: tuple[TestClient, TestClient, InMemoryJobStore, str],
) -> None:
    """After retag, GET /documents/{id}/tags must return the inferred tags.

    Regression guard for BUG-2026-05-25-retag-tags-not-visible: retag wrote
    document tags but the admin UI had no read path to display them.
    """
    write_client_api, _dm_client, _store, document_id = retag_clients

    retag_resp = write_client_api.post(f"/internal/v1/documents/{document_id}/retag")
    assert retag_resp.status_code == HTTPStatus.OK

    tags_resp = write_client_api.get(f"/internal/v1/documents/{document_id}/tags")
    assert tags_resp.status_code == HTTPStatus.OK, (
        f"GET /documents/{{id}}/tags should return 200 after retag; got {tags_resp.status_code}"
    )
    tag_slugs = sorted(
        json_str(as_json_object(tag), "slug")
        for tag in json_list(response_json_object(tags_resp), "tags")
    )
    assert tag_slugs == ["benefits"], (
        f"Expected retag to produce ['benefits'] via GET endpoint; got {tag_slugs}"
    )

"""UJ-053 / TC-161-163, TC-166: corpus rebuild enqueue via POST /jobs (F41 / EV-015).

Drives the data-management ASGI app end-to-end: enqueue rebuild -> runner completes ->
GET /jobs and GET /jobs/{id} show job_type=rebuild. Store-backed modes do not scrape.
"""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentDetail,
    DocumentListPage,
    DocumentSummary,
)

from tests.helpers.json_response import json_object_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

_PROXY_KEY = "test-proxy-key"
_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_DOC_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_DOC_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        return


class _RebuildWriteClient:
    """Store-backed rebuild mock: list/detail + live/shadow upserts."""

    def __init__(self) -> None:
        self.docs = [
            DocumentSummary(
                document_id=_DOC_A,
                url="https://example.com/a",
                title="Doc A",
                language="en",
            ),
            DocumentSummary(
                document_id=_DOC_B,
                url="https://example.com/b",
                title="Doc B",
                language="en",
            ),
        ]
        self.details = {
            _DOC_A: DocumentDetail(
                document_id=_DOC_A,
                url="https://example.com/a",
                title="Doc A",
                language="en",
                text="Body text for document A rebuild path.",
            ),
            _DOC_B: DocumentDetail(
                document_id=_DOC_B,
                url="https://example.com/b",
                title="Doc B",
                language="en",
                text="Body text for document B rebuild path.",
            ),
        }
        self.live_batches: list[BatchUpsertRequest] = []
        self.shadow_batches: list[object] = []
        self.created_rebuild_runs: list[dict[str, object]] = []
        self.fetch_calls: list[str] = []

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _RebuildWriteClient:
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        _ = event

    def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        missing_body: bool = False,
    ) -> DocumentListPage:
        _ = (page, page_size, missing_body)
        return DocumentListPage(
            items=self.docs,
            page=1,
            page_size=50,
            total=len(self.docs),
        )

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        return self.details[document_id]

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        self.live_batches.append(body)
        chunks = sum(len(doc.chunks) for doc in body.documents)
        return BatchUpsertResponse(upserted_chunks=chunks)

    def upsert_shadow_batch(self, body: object) -> BatchUpsertResponse:
        self.shadow_batches.append(body)
        return BatchUpsertResponse(upserted_chunks=1)

    def create_rebuild_run(self, body: dict[str, object]) -> UUID:
        run_id = uuid4()
        self.created_rebuild_runs.append({**body, "rebuild_run_id": run_id})
        return run_id

    def complete_rebuild_run(self, rebuild_run_id: UUID, *, status: str) -> None:
        _ = (rebuild_run_id, status)

    def close(self) -> None:
        return


@pytest.fixture(autouse=True)
def _auth_env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


@pytest.fixture
def rebuild_stack() -> tuple[TestClient, _RebuildWriteClient, InMemoryJobStore]:
    """TestClient + write mock + job store for rebuild e2e journeys."""
    store = InMemoryJobStore()
    write = _RebuildWriteClient()

    def fetch_document(url: str) -> ScrapedDocument:
        write.fetch_calls.append(url)
        return ScrapedDocument(
            url=url,
            title="Scraped",
            text="Scraped body for rescrape mode only.",
        )

    def runner(job_id: UUID) -> None:
        run_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=write,  # type: ignore[arg-type]
            fetch_document=fetch_document,
        )

    app = create_app(
        store=store,
        require_proxy_auth=True,
        pipeline_runner=runner,
    )
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client, write, store


def test_uj053_enqueue_rebuild_job_completes_and_lists(
    rebuild_stack: tuple[TestClient, _RebuildWriteClient, InMemoryJobStore],
) -> None:
    """TC-161: POST /jobs rebuild returns 202; job completes and is listable."""
    client, write, _store = rebuild_stack
    create = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "force": True,
                "document_ids": [str(_DOC_A)],
            },
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    detail = response_json_object(client.get(f"/jobs/{job_id}"))
    assert detail["status"] == "completed"
    assert json_str(detail, "job_type") == "rebuild"

    listed = response_json_object(client.get("/jobs"))
    assert job_id in {json_str(j, "job_id") for j in json_object_list(listed, "jobs")}
    assert write.live_batches or write.shadow_batches
    assert write.fetch_calls == []


def test_uj053_rebuild_modes_and_force(
    rebuild_stack: tuple[TestClient, _RebuildWriteClient, InMemoryJobStore],
) -> None:
    """TC-162: reembed / rechunk / rescrape accepted with force."""
    client, write, store = rebuild_stack
    for mode in ("reembed", "rechunk", "rescrape"):
        write.fetch_calls.clear()
        create = client.post(
            "/jobs",
            json={
                "urls": [],
                "options": {
                    "job_type": "rebuild",
                    "mode": mode,
                    "force": True,
                    "document_ids": [str(_DOC_A)],
                    "dry_run": True,
                },
            },
        )
        assert create.status_code == HTTPStatus.ACCEPTED, mode
        job_id = UUID(json_str(response_json_object(create), "job_id"))
        record = store.get_job(job_id)
        assert record is not None
        assert record.options["mode"] == mode
        assert record.options["force"] is True
        detail = response_json_object(client.get(f"/jobs/{job_id}"))
        assert detail["status"] == "completed", mode
        if mode == "rescrape":
            assert write.fetch_calls
        else:
            assert write.fetch_calls == []


def test_uj053_scoped_document_ids_rebuild(
    rebuild_stack: tuple[TestClient, _RebuildWriteClient, InMemoryJobStore],
) -> None:
    """TC-166: document_ids limits rebuild to listed docs."""
    client, write, _store = rebuild_stack
    create = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "force": True,
                "dry_run": True,
                "document_ids": [str(_DOC_A)],
            },
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")
    assert response_json_object(client.get(f"/jobs/{job_id}"))["status"] == "completed"

    touched_urls: set[str] = set()
    for batch in write.shadow_batches:
        assert isinstance(batch, BatchUpsertRequest)
        for doc in batch.documents:
            touched_urls.add(str(doc.url))
    assert touched_urls == {"https://example.com/a"}
    assert "https://example.com/b" not in touched_urls


def test_uj053_store_backed_rechunk_does_not_scrape(
    rebuild_stack: tuple[TestClient, _RebuildWriteClient, InMemoryJobStore],
) -> None:
    """TC-163/UJ-053: store-backed rechunk uses body_text path (no URL fetch)."""
    client, write, _store = rebuild_stack
    create = client.post(
        "/jobs",
        json={
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "force": True,
                "document_ids": [str(_DOC_A), str(_DOC_B)],
            },
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")
    assert response_json_object(client.get(f"/jobs/{job_id}"))["status"] == "completed"
    assert write.live_batches
    assert write.fetch_calls == []

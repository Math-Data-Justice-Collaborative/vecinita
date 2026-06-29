"""Shared fixtures for internal write API unit tests."""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    text,
)
from vecinita_embedding_client import (
    EMBEDDING_DIMENSION,
)
from vecinita_shared_schemas.auth import (
    reset_auth_config_for_tests,
)
from vecinita_shared_schemas.db_mapping import (
    sqlalchemy_scalar_one,
)

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_str,
    response_json_list,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * EMBEDDING_DIMENSION


def database_url() -> str:
    """Return the configured database URL, falling back to the local default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def auth_headers() -> dict[str, str]:
    """Return the bearer auth header for the internal API key."""
    return {"Authorization": f"Bearer {_API_KEY}"}


class StubJobsClient:
    """Enqueue retag jobs without calling Modal."""

    def __init__(self) -> None:
        """Initialize with an empty list of enqueued document ids."""
        self.enqueued: list[UUID] = []

    def enqueue_retag(self, document_id: UUID) -> UUID:
        """Record the document id and return a synthetic job id."""
        self.enqueued.append(document_id)
        return uuid.uuid4()


@pytest.fixture
def internal_api_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure auth and database env vars for internal write API tests."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.fixture
def engine(internal_api_env: None) -> Engine:
    """Provide a SQLAlchemy engine after the API env is configured."""
    _ = internal_api_env
    return create_engine(database_url())


@pytest.fixture
def write_client(internal_api_env: None) -> TestClient:
    """Provide a TestClient for the internal write API."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    return TestClient(create_app())


@pytest.fixture
def write_client_with_jobs(internal_api_env: None) -> tuple[TestClient, StubJobsClient]:
    """Provide a TestClient wired to a stub jobs client and the stub itself."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    jobs = StubJobsClient()
    client = TestClient(create_app(jobs_client=jobs))  # type: ignore[arg-type]
    return client, jobs


@pytest.fixture
def seeded_document(engine: Engine) -> Iterator[UUID]:
    """Insert a document with one chunk and embedding; delete after test."""
    doc_url = f"https://unit-write-api-{uuid.uuid4().hex[:10]}.example.com"
    vector_literal = "[" + ",".join(str(v) for v in _EMBEDDING) + "]"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO documents (url, title, language)
                    VALUES (:url, 'Unit test doc', 'en')
                    RETURNING id
                    """
                ),
                {"url": doc_url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
        chunk_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO chunks (document_id, chunk_index, text, token_count)
                    VALUES (:doc_id, 0, 'Unit test chunk text', 10)
                    RETURNING id
                    """
                ),
                {"doc_id": doc_id},
            )
        )
        chunk_id = UUID(str(chunk_id_raw))
        conn.execute(
            text(
                """
                INSERT INTO embeddings (chunk_id, embedding)
                VALUES (:chunk_id, CAST(:embedding AS vector))
                """
            ),
            {"chunk_id": chunk_id, "embedding": vector_literal},
        )
    yield doc_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def upsert_document_via_api(
    client: TestClient,
    *,
    url: str | None = None,
    with_tags: bool = False,
) -> str:
    """POST batch upsert and return document_id from list endpoint."""
    base_url = url or f"https://batch-upsert-{uuid.uuid4().hex[:10]}.example.com"
    doc_url = base_url if base_url.endswith("/") else f"{base_url}/"
    document: dict[str, object] = {
        "url": doc_url,
        "title": "Batch upsert doc",
        "language": "en",
        "chunks": [{"chunk_index": 0, "text": "Upserted chunk body", "embedding": _EMBEDDING}],
    }
    if with_tags:
        document["tags"] = [{"slug": "housing", "label": "Housing", "source": "llm"}]
    response = client.post(
        "/internal/v1/documents/batch",
        json={"documents": [document]},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    listing = client.get("/internal/v1/documents", headers=auth_headers())
    rows = response_json_list(listing)
    doc = find_json_object_by_str(rows, "url", doc_url)
    return json_str(doc, "document_id")

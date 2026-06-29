"""T23.5: bulk retag enqueues jobs per document."""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

from tests.helpers.json_response import json_list, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EXPECTED_BULK_JOB_COUNT = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine() -> Engine:
    """Engine."""
    return create_engine(_database_url())


@pytest.fixture
def client() -> TestClient:
    """Client."""
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY

    class _StubJobsClient:
        def enqueue_retag(self, document_id: uuid.UUID) -> uuid.UUID:
            """Enqueue retag."""
            _ = document_id
            return uuid.uuid4()

    return TestClient(create_app(jobs_client=_StubJobsClient()))  # type: ignore[arg-type]


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def sample_docs(engine: Engine) -> Iterator[list[UUID]]:
    """Sample docs."""
    doc_ids: list[UUID] = []
    with engine.begin() as conn:
        for i in range(2):
            url = f"https://bulk-retag-{uuid.uuid4().hex[:8]}-{i}.example.com"
            doc_id_raw = sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        "INSERT INTO documents (url, title, language) "
                        "VALUES (:url, :title, 'en') RETURNING id"
                    ),
                    {"url": url, "title": f"Bulk Retag Doc {i}"},
                )
            )
            doc_id = UUID(str(doc_id_raw))
            doc_ids.append(doc_id)
    yield doc_ids
    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_bulk_retag_returns_job_ids(client: TestClient, sample_docs: list[UUID]) -> None:
    """Bulk retag returns job ids."""
    resp = client.post(
        "/internal/v1/documents/bulk/retag",
        json={"document_ids": [str(d) for d in sample_docs]},
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.ACCEPTED
    data = response_json_object(resp)
    assert len(json_list(data, "job_ids")) == _EXPECTED_BULK_JOB_COUNT


def test_bulk_retag_max_100(client: TestClient) -> None:
    """Bulk retag max 100."""
    ids = [str(uuid.uuid4()) for _ in range(101)]
    resp = client.post(
        "/internal/v1/documents/bulk/retag",
        json={"document_ids": ids},
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

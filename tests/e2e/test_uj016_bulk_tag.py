"""UJ-016 / TC-055 / AC-E6: bulk tag with add/remove + audit."""

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
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EXPECTED_BULK_SUCCESS_COUNT = 2


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

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def sample_docs(engine: Engine) -> Iterator[list[UUID]]:
    """Sample docs."""
    doc_ids: list[UUID] = []
    with engine.begin() as conn:
        for i in range(2):
            url = f"https://bulk-tag-{uuid.uuid4().hex[:8]}-{i}.example.com"
            doc_id_raw = sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        "INSERT INTO documents (url, title, language) "
                        "VALUES (:url, :title, 'en') RETURNING id"
                    ),
                    {"url": url, "title": f"Bulk Tag Doc {i}"},
                )
            )
            doc_id = UUID(str(doc_id_raw))
            doc_ids.append(doc_id)
    yield doc_ids
    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(
                text("DELETE FROM document_tags WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_bulk_tag_add(client: TestClient, sample_docs: list[UUID]) -> None:
    """Bulk tag add."""
    resp = client.patch(
        "/internal/v1/documents/bulk/tags",
        json={
            "document_ids": [str(d) for d in sample_docs],
            "add_tags": [{"slug": "housing", "label": "Housing"}],
            "remove_tags": [],
        },
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.OK
    data = response_json_object(resp)
    assert data["successes"] == _EXPECTED_BULK_SUCCESS_COUNT
    assert data["failures"] == []


def test_bulk_tag_partial_failure_not_found(client: TestClient, sample_docs: list[UUID]) -> None:
    """Bulk tag partial failure not found."""
    fake_id = str(uuid.uuid4())
    resp = client.patch(
        "/internal/v1/documents/bulk/tags",
        json={
            "document_ids": [str(sample_docs[0]), fake_id],
            "add_tags": [{"slug": "legal", "label": "Legal"}],
        },
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.OK
    data = response_json_object(resp)
    assert data["successes"] == 1
    failures = json_list(data, "failures")
    assert len(failures) == 1
    assert json_str(as_json_object(failures[0]), "id") == fake_id


def test_bulk_tag_emits_audit(client: TestClient, sample_docs: list[UUID], engine: Engine) -> None:
    """Bulk tag emits audit."""
    client.patch(
        "/internal/v1/documents/bulk/tags",
        json={
            "document_ids": [str(d) for d in sample_docs],
            "add_tags": [{"slug": "health", "label": "Health"}],
        },
        headers=_auth(),
    )
    with engine.connect() as conn:
        for doc_id in sample_docs:
            row = conn.execute(
                text(
                    "SELECT event_type FROM audit_log "
                    "WHERE entity_id = :id AND event_type = 'document.tagged'"
                ),
                {"id": doc_id},
            ).first()
            assert row is not None


def test_bulk_tag_max_100(client: TestClient) -> None:
    """Bulk tag max 100."""
    ids = [str(uuid.uuid4()) for _ in range(101)]
    resp = client.patch(
        "/internal/v1/documents/bulk/tags",
        json={"document_ids": ids, "add_tags": [{"slug": "x", "label": "X"}]},
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

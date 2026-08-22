"""EV-031 / F76: corpus language parity stats + document list fields (#245).

[Corpus: feature-list.md §F76]
[Spec: docs/api-contract.md §GET /internal/v1/stats/summary]
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_int,
    json_object_get,
    json_object_list,
    json_str,
    json_str_optional,
    response_document_list_items,
    response_json_object,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_API_KEY = "test-internal-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def client() -> TestClient:
    """Provide internal-write TestClient with auth env configured."""
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    return TestClient(create_app())


@pytest.fixture
def engine() -> Engine:
    """SQLAlchemy engine for parity seed cleanup."""
    return create_engine(_database_url())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def parity_seed(client: TestClient, engine: Engine) -> Iterator[dict[str, str]]:
    """Published EN-only + EN/ES paired documents for parity assertions."""
    slug = uuid.uuid4().hex[:10]
    en_only_url = f"https://ev031-en-only-{slug}.example.com/"
    paired_url = f"https://ev031-paired-{slug}.example.com/"

    en_only = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": en_only_url,
                    "title": "EV-031 EN only",
                    "language": "en",
                    "publish_status": "published",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "English-only parity gap seed.",
                            "embedding": _EMBED_VECTOR,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert en_only.status_code == HTTPStatus.OK
    en_only_id = json_str(
        json_object_list(response_json_object(en_only), "documents")[0],
        "document_id",
    )

    en_paired = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": paired_url,
                    "title": "EV-031 paired EN",
                    "language": "en",
                    "publish_status": "published",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "English paired document.",
                            "embedding": _EMBED_VECTOR,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert en_paired.status_code == HTTPStatus.OK
    en_paired_id = json_str(
        json_object_list(response_json_object(en_paired), "documents")[0],
        "document_id",
    )

    es_paired = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": paired_url,
                    "title": "EV-031 paired ES",
                    "language": "es",
                    "publish_status": "published",
                    "paired_document_id": en_paired_id,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Documento emparejado en español.",
                            "embedding": _EMBED_VECTOR,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert es_paired.status_code == HTTPStatus.OK
    es_paired_id = json_str(
        json_object_list(response_json_object(es_paired), "documents")[0],
        "document_id",
    )

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE documents SET paired_document_id = :es WHERE id = :en"),
            {"es": es_paired_id, "en": en_paired_id},
        )

    ids = {
        "en_only_id": en_only_id,
        "en_paired_id": en_paired_id,
        "es_paired_id": es_paired_id,
        "en_only_url": en_only_url,
        "paired_url": paired_url,
    }
    yield ids

    with engine.begin() as conn:
        for doc_id in (en_only_id, en_paired_id, es_paired_id):
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM chunks WHERE document_id = :id"), {"id": doc_id})
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_ev031_stats_summary_parity_fields(
    client: TestClient,
    parity_seed: dict[str, str],
) -> None:
    """TC-255: stats summary exposes chunk language breakdown and parity gaps."""
    _ = parity_seed
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    assert resp.status_code == HTTPStatus.OK
    summary = response_json_object(resp)
    breakdown = json_object_get(summary, "chunk_language_breakdown")
    assert json_int(breakdown, "en") >= 1
    gaps = json_object_get(summary, "parity_gaps")
    assert json_int(gaps, "en_only") >= 1
    assert json_int(gaps, "es_only") >= 0


def test_ev031_document_list_exposes_pairing(
    client: TestClient,
    parity_seed: dict[str, str],
) -> None:
    """TC-256: document list returns paired_document_id for corpus badges."""
    resp = client.get("/internal/v1/documents?page=1&page_size=100", headers=_auth())
    assert resp.status_code == HTTPStatus.OK
    items = response_document_list_items(resp)
    en_only_row = find_json_object_by_str(items, "document_id", parity_seed["en_only_id"])
    paired_en = find_json_object_by_str(items, "document_id", parity_seed["en_paired_id"])
    assert json_str_optional(en_only_row, "paired_document_id") is None
    assert json_str(paired_en, "paired_document_id") == parity_seed["es_paired_id"]
    assert json_str(paired_en, "publish_status") == "published"

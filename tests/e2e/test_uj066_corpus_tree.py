"""UJ-066 / TC-204: corpus tree nesting + nested source fields (F61).

Local Docker/Postgres waived for T111.3 closeout (S024-D41) — same pattern as S021-D23 /
UJ-061: skip-without-Postgres; CI compose provides DATABASE_URL.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import Final
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.corpus_db_guard import is_local_corpus_database
from tests.helpers.json_response import json_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EMBEDDING = [0.02] * 384
_MIN_DOCS_UNDER_GUIDES: Final[int] = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def _postgres_reachable(url: str) -> bool:
    """Return True when local/CI Postgres accepts connections."""
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except (OperationalError, OSError):
        return False
    finally:
        engine.dispose()
    return True


@pytest.fixture
def write_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Internal-write TestClient with local DB + API key (skip without Postgres)."""
    url = _database_url()
    if not is_local_corpus_database(url):
        pytest.skip(
            "TC-204 seeds local Postgres only — unset staging DATABASE_URL (BUG-2026-08-02 guard)"
        )
    if not _postgres_reachable(url):
        pytest.skip(
            "Postgres unavailable for TC-204 / UJ-066 (start compose postgres / make db-ready)"
        )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", url)
    return TestClient(create_app())


def test_uj066_corpus_tree_domain_path_document_nesting(write_client: TestClient) -> None:
    """TC-204 / AC-SC8+SC11: GET /internal/v1/corpus/tree nests domain→path→document."""
    suffix = uuid4()
    guide_a = f"https://tree.example.com/guides/a-{suffix}.html"
    guide_b = f"https://tree.example.com/guides/b-{suffix}.html"
    other = f"https://other.example.org/index-{suffix}.html"
    docs = [
        {
            "url": guide_a,
            "title": "Guide A",
            "language": "en",
            "chunks": [
                {"chunk_index": 0, "text": "guide a body", "embedding": _EMBEDDING},
            ],
        },
        {
            "url": guide_b,
            "title": "Guide B",
            "language": "en",
            "chunks": [
                {"chunk_index": 0, "text": "guide b body", "embedding": _EMBEDDING},
            ],
        },
        {
            "url": other,
            "title": "Other root",
            "language": "en",
            "chunks": [
                {"chunk_index": 0, "text": "other body", "embedding": _EMBEDDING},
            ],
        },
    ]
    upsert = write_client.post(
        "/internal/v1/documents/batch",
        json={"documents": docs},
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert upsert.status_code == HTTPStatus.OK

    tree = write_client.get(
        "/internal/v1/corpus/tree",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert tree.status_code == HTTPStatus.OK
    body = response_json_object(tree)
    roots = json_list(body, "roots")
    assert roots

    domains = {json_str(as_json_object(root), "label") for root in roots}
    assert "tree.example.com" in domains

    example = next(
        as_json_object(root)
        for root in roots
        if json_str(as_json_object(root), "label") == "tree.example.com"
    )
    assert json_str(example, "kind") == "domain"
    path_nodes = json_list(example, "children")
    assert path_nodes
    guides = as_json_object(path_nodes[0])
    assert json_str(guides, "kind") == "path"
    assert json_str(guides, "label") == "guides"
    documents = json_list(guides, "children")
    assert len(documents) >= _MIN_DOCS_UNDER_GUIDES
    for doc in documents:
        node = as_json_object(doc)
        assert json_str(node, "kind") == "document"
        # AC-SC11: nested source fields on document tree nodes
        assert json_str(node, "source_domain") == "tree.example.com"
        assert json_str(node, "source_path") in {"/guides", "guides"}
        assert "url" in node

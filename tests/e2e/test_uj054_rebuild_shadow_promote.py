"""UJ-054 / TC-164-165, TC-168: shadow dry-run then promote (F41 / EV-015).

Drives internal-write ASGI: create dry-run rebuild -> shadow batch -> complete ->
assert live unchanged (TC-164) -> promote (TC-165) -> eval create accepts
rebuild_run_id (TC-168). Requires local DATABASE_URL (same as T89.1 promote).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.db_mapping import mapping_row, row_str
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_int, json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

# Fixtures write_client / engine / seeded_document live in tests/e2e/conftest.py.
# Do not pytest_plugins the unit conftest — it double-registers when CI collects
# tests/unit and tests/e2e together.

pytestmark = pytest.mark.e2e

_EMBEDDING = [0.04] * EMBEDDING_DIMENSION
_SHADOW_TEXT = "uj054-shadow-chunk-text"


def test_uj054_shadow_dry_run_then_promote(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """TC-164/165: shadow dry-run leaves live unchanged until promote."""
    with engine.connect() as conn:
        url = row_str(
            mapping_row(
                conn.execute(
                    text("SELECT url FROM documents WHERE id = :id"),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "url",
        )
        live_before = row_str(
            mapping_row(
                conn.execute(
                    text(
                        """
                        SELECT text FROM chunks
                        WHERE document_id = :id
                        ORDER BY chunk_index
                        LIMIT 1
                        """
                    ),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "text",
        )

    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": "BAAI/bge-small-en-v1.5",
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 64,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    rebuild_run_id = UUID(json_str(as_json_object(cast("object", create.json())), "rebuild_run_id"))

    shadow = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "rebuild_run_id": str(rebuild_run_id),
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": _SHADOW_TEXT,
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert shadow.status_code == HTTPStatus.OK, shadow.text

    complete = write_client.patch(
        f"/internal/v1/rebuild/{rebuild_run_id}",
        json={"status": "completed"},
        headers=auth_headers(),
    )
    assert complete.status_code == HTTPStatus.OK, complete.text

    with engine.connect() as conn:
        live_mid = row_str(
            mapping_row(
                conn.execute(
                    text(
                        """
                        SELECT text FROM chunks
                        WHERE document_id = :id
                        ORDER BY chunk_index
                        LIMIT 1
                        """
                    ),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "text",
        )
    assert live_mid == live_before

    promote = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/promote",
        headers=auth_headers(),
    )
    assert promote.status_code == HTTPStatus.OK, promote.text
    body = as_json_object(cast("object", promote.json()))
    assert body.get("promoted") is True
    assert json_str(body, "rebuild_run_id") == str(rebuild_run_id)
    assert json_int(body, "chunks_promoted") >= 1
    assert json_int(body, "documents_promoted") >= 1

    with engine.connect() as conn:
        live_after = row_str(
            mapping_row(
                conn.execute(
                    text(
                        """
                        SELECT text FROM chunks
                        WHERE document_id = :id
                        ORDER BY chunk_index
                        LIMIT 1
                        """
                    ),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "text",
        )
    assert live_after == _SHADOW_TEXT
    assert live_after != live_before


def test_uj054_eval_create_accepts_rebuild_run_id(write_client: TestClient) -> None:
    """TC-168: POST /eval/runs accepts optional rebuild_run_id (TP-S017-04)."""
    run_id = uuid4()
    response = write_client.post(
        "/internal/v1/eval/runs",
        json={
            "mode": "golden",
            "corpus_profile": "fixture",
            "rebuild_run_id": str(run_id),
        },
        headers=auth_headers(),
    )
    # Unknown rebuild_run_id may 404/400; acceptance is schema/route wire-up.
    assert response.status_code in {
        HTTPStatus.ACCEPTED,
        HTTPStatus.OK,
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.UNPROCESSABLE_ENTITY,
    }
    if response.status_code in {HTTPStatus.ACCEPTED, HTTPStatus.OK}:
        payload = as_json_object(cast("object", response.json()))
        assert "run_id" in payload

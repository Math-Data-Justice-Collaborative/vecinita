"""T121.1 red — F71 E0 rollback restore via F41 promote (TC-239 / AC-ME9).

API path: promote E1 shadow → create new E0 rechunk rebuild → shadow prior live text →
promote → live text + revision stamps restored to LEGACY_E0.

Requires local DATABASE_URL (compose). Remote CI is unit-only (S027-D34 / S027-D35).

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-239]
[Spec: docs/acceptance-criteria.md §AC-ME9]
[Spec: docs/decisions/evolve-decisions.md §S027-D22]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_shared_schemas.db_mapping import mapping_row, row_str
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_int, json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

_E1 = DEFAULT_EMBEDDING_MODEL_ID
_E0 = LEGACY_E0_EMBEDDING_MODEL_ID
_CHUNK_SIZE = 256
_EMBEDDING = [0.05] * EMBEDDING_DIMENSION
_E1_SHADOW = "f71-e1-promoted-shadow"
_E0_RESTORE = "f71-e0-prior-live-text"


def _create_completed_shadow_run(
    write_client: TestClient,
    *,
    url: str,
    embedding_model_id: str,
    shadow_text: str,
) -> UUID:
    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": embedding_model_id,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": _CHUNK_SIZE,
            "chunk_tokenizer_id": embedding_model_id,
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
                            "text": shadow_text,
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
    return rebuild_run_id


def _promote(write_client: TestClient, rebuild_run_id: UUID) -> dict[str, object]:
    promote = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/promote",
        headers=auth_headers(),
    )
    assert promote.status_code == HTTPStatus.OK, promote.text
    body = as_json_object(cast("object", promote.json()))
    assert body.get("promoted") is True
    assert json_int(body, "chunks_promoted") >= 1
    return body


def _live_chunk_text(engine: Engine, document_id: UUID) -> str:
    with engine.connect() as conn:
        return row_str(
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
                    {"id": document_id},
                )
                .mappings()
                .one()
            ),
            "text",
        )


def _doc_url(engine: Engine, document_id: UUID) -> str:
    with engine.connect() as conn:
        return row_str(
            mapping_row(
                conn.execute(
                    text("SELECT url FROM documents WHERE id = :id"),
                    {"id": document_id},
                )
                .mappings()
                .one()
            ),
            "url",
        )


def _latest_revision_stamps(engine: Engine, document_id: UUID) -> tuple[str, str]:
    with engine.connect() as conn:
        row = mapping_row(
            conn.execute(
                text(
                    """
                    SELECT embedding_model_id, chunk_tokenizer_id
                    FROM document_revisions
                    WHERE document_id = :id
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    return row_str(row, "embedding_model_id"), row_str(row, "chunk_tokenizer_id")


def test_tc239_rollback_restores_prior_e0_live_text_and_stamps(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """TC-239 / AC-ME9: after E1 promote, E0 rebuild+promote restores live text + stamps."""
    url = _doc_url(engine, seeded_document)

    # Seed prior "E0 live" text so restore target is explicit (not seed default).
    e0_run = _create_completed_shadow_run(
        write_client,
        url=url,
        embedding_model_id=_E0,
        shadow_text=_E0_RESTORE,
    )
    _ = _promote(write_client, e0_run)
    assert _live_chunk_text(engine, seeded_document) == _E0_RESTORE
    e0_embed, e0_tok = _latest_revision_stamps(engine, seeded_document)
    assert e0_embed == _E0
    assert e0_tok == _E0

    # Cutover promote to E1
    e1_run = _create_completed_shadow_run(
        write_client,
        url=url,
        embedding_model_id=_E1,
        shadow_text=_E1_SHADOW,
    )
    _ = _promote(write_client, e1_run)
    assert _live_chunk_text(engine, seeded_document) == _E1_SHADOW
    e1_embed, e1_tok = _latest_revision_stamps(engine, seeded_document)
    assert e1_embed == _E1
    assert e1_tok == _E1

    # Rollback: new E0 rebuild (cannot re-promote already-promoted E0 run as restore —
    # promote of status=promoted is idempotent and does not re-copy shadow).
    rollback_run = _create_completed_shadow_run(
        write_client,
        url=url,
        embedding_model_id=_E0,
        shadow_text=_E0_RESTORE,
    )
    _ = _promote(write_client, rollback_run)

    assert _live_chunk_text(engine, seeded_document) == _E0_RESTORE
    restored_embed, restored_tok = _latest_revision_stamps(engine, seeded_document)
    assert restored_embed == _E0
    assert restored_tok == _E0
    assert restored_embed != _E1

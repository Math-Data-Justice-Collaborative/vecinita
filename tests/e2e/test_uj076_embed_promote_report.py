"""T120.1 red - UJ-076 / TC-232,235-236,239,241 multilingual rebuild + F36 report (F71).

API e2e for F71 staging cutover contract:
- rebuild stamps multilingual embedding_model_id + chunk_tokenizer_id (rechunk)
- F36 embed-promote report EN/ES rel+faith vs E0 (+ dense when available)
- promote activates shadow while E0 revision remains queryable

Requires local DATABASE_URL (compose). Remote CI runs unit only (S027-D34).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest
from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_embedding_client.modal_pins import DEFAULT_EMBEDDING_MODEL_ID
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str, sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_int, json_object_get, json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.e2e

_E1_PIN = DEFAULT_EMBEDDING_MODEL_ID  # intfloat/multilingual-e5-small
_CHUNK_SIZE_TOKENS = 256
_EMBEDDING = [0.05] * EMBEDDING_DIMENSION
_SHADOW_TEXT = "uj076-multilingual-shadow-chunk"


def test_tc232_241_rebuild_stamps_multilingual_pin_and_tokenizer(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """TC-232/241: rechunk dry-run stamps E1 embedding_model_id + matching tokenizer."""
    _ = seeded_document
    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": _E1_PIN,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
            "chunk_tokenizer_id": _E1_PIN,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    body = as_json_object(cast("object", create.json()))
    rebuild_run_id = UUID(json_str(body, "rebuild_run_id"))

    with engine.connect() as conn:
        row = mapping_row(
            conn.execute(
                text(
                    """
                    SELECT embedding_model_id, embedding_dim, chunk_size_tokens,
                           chunk_tokenizer_id, mode, dry_run
                    FROM rebuild_runs
                    WHERE id = :id
                    """
                ),
                {"id": rebuild_run_id},
            )
            .mappings()
            .one()
        )
    assert row_str(row, "embedding_model_id") == _E1_PIN
    assert row_str(row, "chunk_tokenizer_id") == _E1_PIN
    assert row_str(row, "mode") == "rechunk"
    assert row_int(row, "embedding_dim") == EMBEDDING_DIMENSION
    assert row_int(row, "chunk_size_tokens") == _CHUNK_SIZE_TOKENS
    assert bool(row["dry_run"]) is True


def test_tc235_236_embed_promote_report_en_es_vs_e0(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """TC-235/236: GET embed-promote report has EN/ES Hy1 metrics (+ dense when flagged)."""
    _ = (engine, seeded_document)
    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "completed",
            "embedding_model_id": _E1_PIN,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
            "chunk_tokenizer_id": _E1_PIN,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    rebuild_run_id = json_str(as_json_object(cast("object", create.json())), "rebuild_run_id")

    report = write_client.get(
        f"/internal/v1/rebuild/{rebuild_run_id}/embed-promote-report",
        headers=auth_headers(),
    )
    assert report.status_code == HTTPStatus.OK, report.text
    payload = as_json_object(cast("object", report.json()))
    assert json_str(payload, "candidate_embedding_model_id") == _E1_PIN
    assert json_str(payload, "baseline_embedding_model_id")  # E0 pin retained for compare
    by_lang = json_object_get(payload, "by_language")
    for lang in ("en", "es"):
        lang_metrics = json_object_get(by_lang, lang)
        assert "answer_relevancy" in lang_metrics
        assert "faithfulness" in lang_metrics
        assert "baseline_e0" in lang_metrics
        baseline = json_object_get(lang_metrics, "baseline_e0")
        assert "answer_relevancy" in baseline
        assert "faithfulness" in baseline
    if payload.get("dense_available") is True:
        for lang in ("en", "es"):
            lang_metrics = json_object_get(by_lang, lang)
            assert "hit_at_k" in lang_metrics
            assert "mean_rank" in lang_metrics


def test_tc239_promote_activates_shadow_e0_revision_retained(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """TC-239: promote swaps live text; prior E0 revision remains on document_revisions."""
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
            "embedding_model_id": _E1_PIN,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
            "chunk_tokenizer_id": _E1_PIN,
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

    promote = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/promote",
        headers=auth_headers(),
    )
    assert promote.status_code == HTTPStatus.OK, promote.text
    promote_body = as_json_object(cast("object", promote.json()))
    assert promote_body.get("promoted") is True
    assert json_int(promote_body, "chunks_promoted") >= 1

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
        e0_revisions = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS n
                    FROM document_revisions
                    WHERE document_id = :id
                      AND (
                        embedding_model_id IS DISTINCT FROM :e1
                        OR embedding_model_id IS NULL
                      )
                    """
                ),
                {"id": seeded_document, "e1": _E1_PIN},
            )
        )
        e1_revisions = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS n
                    FROM document_revisions
                    WHERE document_id = :id
                      AND embedding_model_id = :e1
                      AND chunk_tokenizer_id = :e1
                    """
                ),
                {"id": seeded_document, "e1": _E1_PIN},
            )
        )

    assert live_after == _SHADOW_TEXT
    assert live_after != live_before
    assert isinstance(e0_revisions, int)
    assert isinstance(e1_revisions, int)
    assert e0_revisions >= 1  # prior E0 restorable
    assert e1_revisions >= 1  # new pin stamped

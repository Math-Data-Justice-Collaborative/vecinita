"""Duplicate pipeline POSTs must not create duplicate embeddings (data-model idempotency)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


def test_store_embeddings_sql_uses_on_conflict_do_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    monkeypatch.setattr(persist, "Json", lambda d: d)

    mock_cur = MagicMock()
    mock_cur.rowcount = 1

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    cid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    persist.store_embeddings(
        "job-1",
        [
            {
                "chunk_id": cid,
                "embedding": [0.1, 0.2],
                "model_name": "m1",
                "dimensions": 2,
            },
            {
                "chunk_id": cid,
                "embedding": [0.3, 0.4],
                "model_name": "m1",
                "dimensions": 2,
            },
        ],
    )

    assert mock_cur.execute.call_count == 2
    for call in mock_cur.execute.call_args_list:
        sql = call[0][0]
        assert "ON CONFLICT (chunk_id, model_name) DO NOTHING" in sql


def test_store_chunks_persists_raw_and_enriched_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    mock_cur = MagicMock()

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    pid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    persist.store_chunks(
        pid,
        [
            {
                "text": "display",
                "raw_text": "raw segment",
                "enriched_text": "enriched segment",
                "position": 0,
            }
        ],
    )

    sql = mock_cur.execute.call_args[0][0]
    assert "raw_text" in sql and "enriched_text" in sql
    params = mock_cur.execute.call_args[0][1]
    # id, processed_doc_id, chunk_text, position, token_count, semantic_boundary, raw_text, enriched_text
    assert params[2] == "display"
    assert params[6] == "raw segment"
    assert params[7] == "enriched segment"

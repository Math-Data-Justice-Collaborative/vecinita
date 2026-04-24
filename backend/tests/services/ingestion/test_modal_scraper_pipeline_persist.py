"""Unit tests for ``modal_scraper_pipeline_persist`` helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


def test_update_job_status_raises_when_no_matching_row(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    mock_cur = MagicMock()
    mock_cur.rowcount = 0

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    with pytest.raises(RuntimeError, match="0 rows"):
        persist.update_job_status("nonexistent-job-id", "failed", "boom")

    mock_cur.execute.assert_called_once()


def test_update_job_status_merges_pipeline_stage_into_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist
    from src.services.ingestion import pipeline_stage as ps

    monkeypatch.setattr(persist, "Json", lambda d: d)

    mock_cur = MagicMock()
    mock_cur.rowcount = 1
    mock_cur.fetchone.return_value = {"metadata": {}}

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    persist.update_job_status(
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "crawling",
        None,
        pipeline_stage=ps.PIPELINE_STAGE_SCRAPING,
    )

    assert mock_cur.execute.call_count == 2
    second_sql = mock_cur.execute.call_args_list[1][0][0]
    assert "metadata = %s" in second_sql


def test_update_job_status_rejects_invalid_pipeline_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist
    from src.services.ingestion import pipeline_stage as ps

    monkeypatch.setattr(persist, "Json", lambda d: d)

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"metadata": {"pipeline_stage": "scraping"}}

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    with pytest.raises(ValueError, match="not allowed"):
        persist.update_job_status(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "embedding",
            None,
            pipeline_stage=ps.PIPELINE_STAGE_EMBEDDING,
        )


def test_store_crawled_url_upsert_returns_id_from_returning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    stable_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"id": stable_id}

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    out = persist.store_crawled_url(
        "job-1",
        "https://example.com/",
        raw_content="ignored",
        content_hash="0" * 64,
        status="failed",
        error_message="blocked",
    )
    assert out == stable_id
    mock_cur.execute.assert_called_once()
    sql = mock_cur.execute.call_args[0][0]
    assert "ON CONFLICT (job_id, url)" in sql
    assert "RETURNING id" in sql


def test_store_crawled_url_idempotent_replay_returns_same_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate two ingest calls (e.g. Modal retry): both receive the same RETURNING id."""
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    stable_id = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"id": stable_id}

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    args = (
        "job-retry",
        "https://health.ri.gov/",
        "",
        "c" * 64,
        "failed",
        "anti-bot",
    )
    assert persist.store_crawled_url(*args) == stable_id
    assert persist.store_crawled_url(*args) == stable_id
    assert mock_cur.execute.call_count == 2


def test_store_crawled_url_raises_when_returning_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist as persist

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(persist, "_connect", lambda: mock_conn)

    with pytest.raises(RuntimeError, match="did not return id"):
        persist.store_crawled_url("j", "https://x.test/", "", "d" * 64)

"""T038: canonical URL dedup against terminal **completed** jobs (modal_scraper_persist)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


def test_find_completed_scrape_job_duplicate_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.ingestion import modal_scraper_persist as ms

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(ms, "_connect", lambda: mock_conn)

    out = ms.find_completed_scrape_job_duplicate("user-1", "https://example.com/a")
    assert out == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    sql = mock_cur.execute.call_args[0][0]
    assert "lower(trim(url))" in sql
    assert "lower(status) = 'completed'" in sql


def test_create_scraping_job_duplicate_skipped_inserts_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.services.ingestion import modal_scraper_persist as ms

    monkeypatch.setattr(ms, "Json", lambda d: d)

    mock_cur = MagicMock()

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = mock_cur
    cursor_cm.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_cm

    monkeypatch.setattr(ms, "_connect", lambda: mock_conn)

    jid = ms.create_scraping_job_duplicate_skipped(
        url="https://Example.COM/a ",
        user_id="user-1",
        crawl_config={},
        chunking_config={},
        metadata={"correlation_id": "c1"},
        prior_completed_job_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    )
    assert len(jid) == 36
    insert_sql = mock_cur.execute.call_args[0][0]
    assert "INSERT INTO scraping_jobs" in insert_sql
    params = mock_cur.execute.call_args[0][1]
    assert params[3] == "completed"
    meta = params[6]
    assert meta["pipeline_stage"] == "duplicate_skipped"
    assert meta["dedup_of_job_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

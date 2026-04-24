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

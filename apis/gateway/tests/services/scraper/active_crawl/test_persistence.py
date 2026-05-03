"""Persistence SQL parameter shaping (mocked DB)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID

from src.services.scraper.active_crawl.persistence import CrawlRepository, FetchAttemptRow


@contextmanager
def _fake_conn(cur: MagicMock):
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    yield conn


def test_create_run_executes_insert_with_jsonb() -> None:
    cur = MagicMock()
    cur.fetchone.return_value = ("550e8400-e29b-41d4-a716-446655440000",)
    conn_cm = _fake_conn(cur)

    with patch(
        "src.services.scraper.active_crawl.persistence.psycopg2.connect", return_value=conn_cm
    ):
        repo = CrawlRepository(database_url="postgresql://localhost/test")
        rid = repo.create_run({"k": 1}, initiator="cli")

    assert isinstance(rid, UUID)
    assert cur.execute.called
    args = cur.execute.call_args[0]
    assert "INSERT INTO crawl_runs" in args[0]
    assert '"k": 1' in args[1][0]


def test_insert_fetch_attempt_passes_row_fields() -> None:
    cur = MagicMock()
    conn_cm = _fake_conn(cur)
    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    row = FetchAttemptRow(
        crawl_run_id=run_id,
        canonical_url="https://x/",
        requested_url="https://x/",
        final_url="https://x/",
        seed_root="x",
        depth=0,
        http_status=200,
        outcome="success",
        skip_reason=None,
        retrieval_path="static",
        document_format="html",
        extracted_text="hi",
        raw_artifact=b"raw",
        raw_omitted_reason=None,
        content_sha256="abc",
        pdf_extraction_status="na",
        error_detail=None,
    )

    with patch(
        "src.services.scraper.active_crawl.persistence.psycopg2.connect", return_value=conn_cm
    ):
        repo = CrawlRepository(database_url="postgresql://localhost/test")
        with patch("src.services.scraper.active_crawl.persistence.datetime") as dt_mod:
            dt_mod.now.return_value = datetime(2020, 1, 1, tzinfo=timezone.utc)
            repo.insert_fetch_attempt(row)

    sql, params = cur.execute.call_args[0]
    assert "INSERT INTO crawl_fetch_attempts" in sql
    assert params[0] == str(run_id)
    assert params[1] == "https://x/"
    assert params[13] == b"raw"

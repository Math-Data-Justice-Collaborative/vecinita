from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src.agent.utils.vector_loader import DocumentChunk as LoaderChunk
from src.agent.utils.vector_loader import VecinitaLoader
from src.services.scraper.uploader import DatabaseUploader

pytestmark = pytest.mark.integration


class _FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.executed.append((sql, params or ()))

    def fetchone(self):
        return ("00000000-0000-0000-0000-000000000001",)


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor


@pytest.fixture
def postgres_env(monkeypatch):
    monkeypatch.setenv("DB_DATA_MODE", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db?sslmode=require")
    monkeypatch.setenv("VECTOR_SYNC_TARGET", "postgres")
    monkeypatch.setenv("VECTOR_SYNC_ENABLED", "true")
    monkeypatch.setenv("VECTOR_SYNC_DEGRADED_MODE", "false")
    monkeypatch.setenv("VECTOR_SYNC_RETRY_MAX", "1")


def test_postgres_cutover_loader_and_uploader_paths(postgres_env, monkeypatch):
    loader_cursor = _FakeCursor()
    uploader_cursor = _FakeCursor()

    def _loader_connect(*_args, **_kwargs):
        return _FakeConnection(loader_cursor)

    def _uploader_connect(*_args, **_kwargs):
        return _FakeConnection(uploader_cursor)

    monkeypatch.setattr("src.agent.utils.vector_loader.USE_LOCAL_EMBEDDINGS", False)
    monkeypatch.setattr("src.agent.utils.vector_loader.POSTGRES_AVAILABLE", True)
    monkeypatch.setattr(
        "src.agent.utils.vector_loader.psycopg2", SimpleNamespace(connect=_loader_connect)
    )
    loader = VecinitaLoader()

    # Avoid embedding generation dependency for this integration path assertion.
    loader.generate_embedding = Mock(return_value=[0.1] * 384)
    success, failed = loader.process_batch(
        [
            LoaderChunk(
                content="render postgres loader chunk",
                source_url="https://example.org/loader",
                chunk_index=1,
                total_chunks=1,
                document_id="00000000-0000-0000-0000-0000000000ab",
                scraped_at=datetime.now(timezone.utc),
                metadata={"tags": ["housing"]},
            )
        ]
    )

    assert success == 1
    assert failed == 0
    assert any("INSERT INTO document_chunks" in sql for sql, _ in loader_cursor.executed)

    with (
        patch.object(DatabaseUploader, "_init_embeddings"),
        patch.object(DatabaseUploader, "_init_local_llm_tagger"),
        patch.object(DatabaseUploader, "_init_supabase"),
    ):
        monkeypatch.setattr("src.services.scraper.uploader.POSTGRES_AVAILABLE", True)
        monkeypatch.setattr(
            "src.services.scraper.uploader.psycopg2", SimpleNamespace(connect=_uploader_connect)
        )
        uploader = DatabaseUploader(use_local_embeddings=False)

    uploader.chroma_store = Mock()
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.chroma_store.list_sources.return_value = []
    uploader.chroma_store.get_source.return_value = None
    uploader.local_llm_tagger = None
    uploader.local_llm_raw_model = None
    uploader._generate_embeddings = Mock(return_value=[[0.2] * 384])

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "render postgres uploader chunk", "metadata": {}}],
        source_identifier="https://example.org/uploader",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    assert any("INSERT INTO document_chunks" in sql for sql, _ in uploader_cursor.executed)

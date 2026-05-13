import asyncio
from types import SimpleNamespace

import pytest

from src.services.db import pool

pytestmark = pytest.mark.unit


class _FakeCursor:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def execute(self, _query):
        if self.should_fail:
            raise RuntimeError("query failed")

    def fetchone(self):
        return (1,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def cursor(self):
        return _FakeCursor(should_fail=self.should_fail)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.anyio
async def test_initialize_raises_when_config_missing(monkeypatch):
    db_pool = pool.DatabaseConnectionPool()
    monkeypatch.setattr(pool, "DATABASE_URL", "")

    with pytest.raises(RuntimeError):
        await db_pool.initialize()


@pytest.mark.anyio
async def test_initialize_sets_client_and_status(monkeypatch):
    db_pool = pool.DatabaseConnectionPool()
    monkeypatch.setattr(pool, "DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setattr(
        pool, "psycopg2", SimpleNamespace(connect=lambda *_args, **_kwargs: _FakeConnection())
    )

    async def _fake_health_loop():
        await asyncio.sleep(0)

    monkeypatch.setattr(db_pool, "_run_health_checks", _fake_health_loop)

    await db_pool.initialize()

    assert db_pool._initialized is True
    assert db_pool._health_status["connected"] is True

    await db_pool.shutdown()


def test_get_client_requires_initialization():
    db_pool = pool.DatabaseConnectionPool()

    with pytest.raises(RuntimeError):
        db_pool.get_client()


@pytest.mark.anyio
async def test_health_check_returns_false_without_client():
    db_pool = pool.DatabaseConnectionPool()

    assert await db_pool.health_check() is False


@pytest.mark.anyio
async def test_health_check_success_updates_status():
    db_pool = pool.DatabaseConnectionPool()
    db_pool._client = "postgresql://user:pass@localhost:5432/db"
    original_psycopg2 = pool.psycopg2
    pool.psycopg2 = SimpleNamespace(connect=lambda *_args, **_kwargs: _FakeConnection())

    try:
        assert await db_pool.health_check() is True
        assert db_pool._health_status["connected"] is True
    finally:
        pool.psycopg2 = original_psycopg2


@pytest.mark.anyio
async def test_health_check_failure_updates_status():
    db_pool = pool.DatabaseConnectionPool()
    db_pool._client = "postgresql://user:pass@localhost:5432/db"
    original_psycopg2 = pool.psycopg2
    pool.psycopg2 = SimpleNamespace(
        connect=lambda *_args, **_kwargs: _FakeConnection(should_fail=True)
    )

    try:
        assert await db_pool.health_check() is False
        assert db_pool._health_status["connected"] is False
    finally:
        pool.psycopg2 = original_psycopg2


@pytest.mark.anyio
async def test_query_with_timeout_success_updates_success_counter(monkeypatch):
    original_success = pool.connection_pool._health_status["successful_queries"]

    async with pool.query_with_timeout("ok-query"):
        pass

    assert pool.connection_pool._health_status["successful_queries"] == original_success + 1


@pytest.mark.anyio
async def test_query_with_timeout_timeout_updates_failure_counter():
    original_failed = pool.connection_pool._health_status["failed_queries"]

    with pytest.raises(asyncio.TimeoutError):
        async with pool.query_with_timeout("timeout-query"):
            raise asyncio.TimeoutError()

    assert pool.connection_pool._health_status["failed_queries"] == original_failed + 1


@pytest.mark.anyio
async def test_execute_with_retry_sync_query_succeeds():
    calls = {"count": 0}

    def _query():
        calls["count"] += 1
        return {"ok": True}

    result = await pool.execute_with_retry(_query, query_name="sync-query", max_attempts=2)

    assert result == {"ok": True}
    assert calls["count"] == 1


@pytest.mark.anyio
async def test_execute_with_retry_async_query_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    async def _query():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("first failure")
        return "ok"

    monkeypatch.setattr(pool, "QUERY_RETRY_BACKOFF_SECONDS", 0)

    result = await pool.execute_with_retry(_query, query_name="async-query", max_attempts=2)

    assert result == "ok"
    assert calls["count"] == 2


@pytest.mark.anyio
async def test_execute_with_retry_raises_last_error(monkeypatch):
    async def _query():
        raise RuntimeError("always fails")

    monkeypatch.setattr(pool, "QUERY_RETRY_BACKOFF_SECONDS", 0)

    with pytest.raises(RuntimeError, match="always fails"):
        await pool.execute_with_retry(_query, query_name="fail-query", max_attempts=2)


def test_get_stats_returns_expected_shape():
    db_pool = pool.DatabaseConnectionPool()

    stats = db_pool.get_stats()

    assert "initialized" in stats
    assert "connected" in stats
    assert "stats" in stats

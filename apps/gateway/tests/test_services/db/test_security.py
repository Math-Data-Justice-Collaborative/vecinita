import asyncio
from types import SimpleNamespace

import pytest

from src.services.db import security

pytestmark = pytest.mark.unit


def test_validate_table_name_accepts_valid_name():
    assert security.QueryValidator.validate_table_name("document_chunks") == "document_chunks"


@pytest.mark.parametrize("value", ["", "bad;name", "bad name", "bad'name"])
def test_validate_table_name_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        security.QueryValidator.validate_table_name(value)


def test_validate_column_name_accepts_dot_notation():
    assert security.QueryValidator.validate_column_name("metadata.source") == "metadata.source"


@pytest.mark.parametrize("value", ["", "bad-name", "bad name", "bad;"])
def test_validate_column_name_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        security.QueryValidator.validate_column_name(value)


def test_validate_filter_value_accepts_supported_types():
    value = {"a": [1, "x", None, True, {"nested": 1.5}]}
    assert security.QueryValidator.validate_filter_value(value) == value


def test_validate_filter_value_rejects_unsupported_type():
    class _Bad:
        pass

    with pytest.raises(ValueError):
        security.QueryValidator.validate_filter_value(_Bad())


def test_query_audit_logs_slow_query(monkeypatch):
    calls = {"slow": 0}

    monkeypatch.setattr(
        security.slow_query_logger,
        "warning",
        lambda *_args, **_kwargs: calls.__setitem__("slow", calls["slow"] + 1),
    )
    monkeypatch.setattr(security, "ENABLE_QUERY_LOGGING", False)

    security.QueryAudit.log_query("select", "documents", 10.0, True)

    assert calls["slow"] == 1


@pytest.mark.anyio
async def test_track_query_time_async_success(monkeypatch):
    calls = {"ok": 0}

    def _log_query(*_args, **_kwargs):
        calls["ok"] += 1

    monkeypatch.setattr(security.QueryAudit, "log_query", _log_query)

    @security.track_query_time("select", "documents")
    async def _fn():
        await asyncio.sleep(0)
        return "done"

    result = await _fn()

    assert result == "done"
    assert calls["ok"] == 1


def test_track_query_time_sync_failure(monkeypatch):
    calls = {"count": 0}

    def _log_query(*_args, **_kwargs):
        calls["count"] += 1

    monkeypatch.setattr(security.QueryAudit, "log_query", _log_query)

    @security.track_query_time("delete", "documents")
    def _fn():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        _fn()

    assert calls["count"] == 1


class _DeleteQuery:
    def __init__(self, data=None):
        self._data = data if data is not None else [{"id": 1}, {"id": 2}]

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


class _DeleteTable:
    def delete(self):
        return _DeleteQuery()


class _DeleteDB:
    def table(self, _name):
        return _DeleteTable()


@pytest.mark.anyio
async def test_delete_documents_by_filter_returns_deleted_count():
    count = await security.delete_documents_by_filter(
        _DeleteDB(),
        table_name="documents",
        filter_field="source",
        filter_value="abc",
        session_id="session-1",
    )

    assert count == 2


class _SingleQuery:
    def __init__(self, data):
        self._data = data

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


class _SingleDB:
    def __init__(self, data):
        self._data = data

    def table(self, _name):
        return self

    def select(self, *_args, **_kwargs):
        return _SingleQuery(self._data)


@pytest.mark.anyio
async def test_get_document_by_id_returns_data():
    result = await security.get_document_by_id(_SingleDB({"id": "doc-1"}), "doc-1")
    assert result == {"id": "doc-1"}


@pytest.mark.anyio
async def test_get_document_by_id_propagates_exception():
    class _FailDB:
        def table(self, _name):
            raise RuntimeError("db down")

    with pytest.raises(RuntimeError):
        await security.get_document_by_id(_FailDB(), "doc-1")


def test_suggest_indexes_returns_recommendations():
    slow_queries = ["documents_by_source"] * 11 + ["other"] * 2
    suggestions = security.suggest_indexes(slow_queries)

    assert any("documents_by_source" in item for item in suggestions)

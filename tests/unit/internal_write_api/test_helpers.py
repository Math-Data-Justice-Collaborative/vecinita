"""Unit tests for internal write API helper functions."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from vecinita_internal_write_api.app import (
    _dependency_health_url,
    _normalize_database_url,
    _require_internal_key,
    _row_datetime,
    _row_datetime_optional,
    _tags_snapshot_list,
)


def test_dependency_health_url_appends_health() -> None:
    assert _dependency_health_url("http://svc:8000") == "http://svc:8000/health"


def test_dependency_health_url_preserves_existing_health_suffix() -> None:
    assert _dependency_health_url("http://svc:8000/health") == "http://svc:8000/health"


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_normalize_database_url_leaves_psycopg_unchanged() -> None:
    url = "postgresql+psycopg://user:pass@host/db"
    assert _normalize_database_url(url) == url


def test_row_datetime_returns_datetime() -> None:
    now = datetime.now(UTC)
    assert _row_datetime({"created_at": now}, "created_at") == now


def test_row_datetime_raises_on_wrong_type() -> None:
    with pytest.raises(TypeError, match="Expected datetime"):
        _row_datetime({"created_at": "not-a-datetime"}, "created_at")


def test_row_datetime_optional_returns_none() -> None:
    assert _row_datetime_optional({"last_served_at": None}, "last_served_at") is None


def test_row_datetime_optional_returns_datetime() -> None:
    now = datetime.now(UTC)
    assert _row_datetime_optional({"last_served_at": now}, "last_served_at") == now


def test_tags_snapshot_list_filters_non_dict_items() -> None:
    snapshots = _tags_snapshot_list([{"slug": "housing"}, "skip", 42])
    assert snapshots == [{"slug": "housing"}]


def test_tags_snapshot_list_returns_empty_for_non_list() -> None:
    assert _tags_snapshot_list({"not": "a list"}) == []


def test_require_internal_key_skips_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VECINITA_INTERNAL_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        _require_internal_key(authorization="Bearer anything")
    assert exc.value.status_code == 503


def test_require_internal_key_rejects_missing_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "expected")
    with pytest.raises(HTTPException) as exc:
        _require_internal_key(authorization=None)
    assert exc.value.status_code == 401


def test_require_internal_key_rejects_wrong_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "expected")
    with pytest.raises(HTTPException) as exc:
        _require_internal_key(authorization="Bearer wrong")
    assert exc.value.status_code == 401


def test_require_internal_key_accepts_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "expected")
    _require_internal_key(authorization="Bearer expected")

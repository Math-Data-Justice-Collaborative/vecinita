"""Unit tests for internal write API helper functions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from starlette.requests import Request
from vecinita_internal_write_api.app import (
    _dependency_health_url,  # pyright: ignore[reportPrivateUsage]
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
    _resolve_write_actor,  # pyright: ignore[reportPrivateUsage]
    _row_datetime,  # pyright: ignore[reportPrivateUsage]
    _row_datetime_optional,  # pyright: ignore[reportPrivateUsage]
    _tags_snapshot_list,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_shared_schemas.auth import AuthContext, AuthPrincipal


def test_dependency_health_url_appends_health() -> None:
    """Test dependency health url appends health."""
    assert _dependency_health_url("http://svc:8000") == "http://svc:8000/health"


def test_dependency_health_url_preserves_existing_health_suffix() -> None:
    """Test dependency health url preserves existing health suffix."""
    assert _dependency_health_url("http://svc:8000/health") == "http://svc:8000/health"


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    """Test normalize database url upgrades postgresql scheme."""
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_normalize_database_url_leaves_psycopg_unchanged() -> None:
    """Test normalize database url leaves psycopg unchanged."""
    url = "postgresql+psycopg://user:pass@host/db"
    assert _normalize_database_url(url) == url


def test_row_datetime_returns_datetime() -> None:
    """Test row datetime returns datetime."""
    now = datetime.now(UTC)
    assert _row_datetime({"created_at": now}, "created_at") == now


def test_row_datetime_raises_on_wrong_type() -> None:
    """Test row datetime raises on wrong type."""
    with pytest.raises(TypeError, match="Expected datetime"):
        _row_datetime({"created_at": "not-a-datetime"}, "created_at")


def test_row_datetime_optional_returns_none() -> None:
    """Test row datetime optional returns none."""
    assert _row_datetime_optional({"last_served_at": None}, "last_served_at") is None


def test_row_datetime_optional_returns_datetime() -> None:
    """Test row datetime optional returns datetime."""
    now = datetime.now(UTC)
    assert _row_datetime_optional({"last_served_at": now}, "last_served_at") == now


def test_tags_snapshot_list_filters_non_dict_items() -> None:
    """Test tags snapshot list filters non dict items."""
    snapshots = _tags_snapshot_list([{"slug": "housing"}, "skip", 42])
    assert snapshots == [{"slug": "housing"}]


def test_tags_snapshot_list_returns_empty_for_non_list() -> None:
    """Test tags snapshot list returns empty for non list."""
    assert _tags_snapshot_list({"not": "a list"}) == []


def _empty_request() -> Request:
    """Minimal Starlette request for helper unit tests."""
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


def test_resolve_write_actor_returns_principal_sub_and_role() -> None:
    """Operator writes attribute audit rows to the principal's sub and role."""
    sub = uuid4()
    ctx = AuthContext(principal=AuthPrincipal(sub=sub, role="admin"), is_service=False)
    assert _resolve_write_actor(ctx, _empty_request()) == (sub, "admin")


def test_resolve_write_actor_returns_none_for_service_caller() -> None:
    """Service-key writes carry no operator attribution."""
    ctx = AuthContext(principal=None, is_service=True)
    assert _resolve_write_actor(ctx, _empty_request()) == (None, None)

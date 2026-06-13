"""Unit tests for ChatRagSettings and env helpers."""

from __future__ import annotations

import pytest
from vecinita_chat_rag_backend.config import (
    ChatRagSettings,
    _bool_env,
    _float_env,
    _int_env,
    _normalize_database_url,
)


def test_int_env_returns_default_when_missing() -> None:
    assert _int_env("VECINITA_TEST_INT_MISSING", 7) == 7


def test_int_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_TEST_INT", "12")
    assert _int_env("VECINITA_TEST_INT", 7) == 12


def test_float_env_returns_default_when_missing() -> None:
    assert _float_env("VECINITA_TEST_FLOAT_MISSING", 0.5) == 0.5


def test_float_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_TEST_FLOAT", "0.75")
    assert _float_env("VECINITA_TEST_FLOAT", 0.5) == 0.75


def test_bool_env_defaults_when_missing() -> None:
    assert _bool_env("VECINITA_TEST_BOOL_MISSING", True) is True
    assert _bool_env("VECINITA_TEST_BOOL_MISSING_FALSE", False) is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE"])
def test_bool_env_parses_truthy(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_TEST_BOOL", value)
    assert _bool_env("VECINITA_TEST_BOOL", False) is True


def test_bool_env_parses_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_TEST_BOOL", "0")
    assert _bool_env("VECINITA_TEST_BOOL", True) is False


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_from_env_builds_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_TOP_K", "3")
    monkeypatch.setenv("VECINITA_MIN_RETRIEVAL_SCORE", "0.3")
    monkeypatch.setenv("VECINITA_STATS_ENABLED", "false")
    settings = ChatRagSettings.from_env()
    assert settings.top_k == 3
    assert settings.min_retrieval_score == 0.3
    assert settings.stats_enabled is False
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_from_env_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        ChatRagSettings.from_env()

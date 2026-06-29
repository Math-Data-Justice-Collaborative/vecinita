"""Unit tests for ChatRagSettings and env helpers."""

from __future__ import annotations

import pytest
from vecinita_chat_rag_backend.config import (
    ChatRagSettings,
    _bool_env,  # pyright: ignore[reportPrivateUsage]
    _float_env,  # pyright: ignore[reportPrivateUsage]
    _int_env,  # pyright: ignore[reportPrivateUsage]
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
)

_DEFAULT_INT = 7
_PARSED_INT = 12
_DEFAULT_FLOAT = 0.5
_PARSED_FLOAT = 0.75
_ENV_TOP_K = 3
_ENV_MIN_SCORE = 0.3


def test_int_env_returns_default_when_missing() -> None:
    """Test int env returns default when missing."""
    assert _int_env("VECINITA_TEST_INT_MISSING", _DEFAULT_INT) == _DEFAULT_INT


def test_int_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test int env parses value."""
    monkeypatch.setenv("VECINITA_TEST_INT", "12")
    assert _int_env("VECINITA_TEST_INT", _DEFAULT_INT) == _PARSED_INT


def test_float_env_returns_default_when_missing() -> None:
    """Test float env returns default when missing."""
    assert _float_env("VECINITA_TEST_FLOAT_MISSING", _DEFAULT_FLOAT) == _DEFAULT_FLOAT


def test_float_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test float env parses value."""
    monkeypatch.setenv("VECINITA_TEST_FLOAT", "0.75")
    assert _float_env("VECINITA_TEST_FLOAT", _DEFAULT_FLOAT) == _PARSED_FLOAT


def test_bool_env_defaults_when_missing() -> None:
    """Test bool env defaults when missing."""
    assert _bool_env("VECINITA_TEST_BOOL_MISSING", default=True) is True
    assert _bool_env("VECINITA_TEST_BOOL_MISSING_FALSE", default=False) is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE"])
def test_bool_env_parses_truthy(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test bool env parses truthy."""
    monkeypatch.setenv("VECINITA_TEST_BOOL", value)
    assert _bool_env("VECINITA_TEST_BOOL", default=False) is True


def test_bool_env_parses_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test bool env parses false."""
    monkeypatch.setenv("VECINITA_TEST_BOOL", "0")
    assert _bool_env("VECINITA_TEST_BOOL", default=True) is False


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    """Test normalize database url upgrades postgresql scheme."""
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_from_env_builds_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test from env builds settings."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_TOP_K", "3")
    monkeypatch.setenv("VECINITA_MIN_RETRIEVAL_SCORE", "0.3")
    monkeypatch.setenv("VECINITA_STATS_ENABLED", "false")
    settings = ChatRagSettings.from_env()
    assert settings.top_k == _ENV_TOP_K
    assert settings.min_retrieval_score == _ENV_MIN_SCORE
    assert settings.stats_enabled is False
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_from_env_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test from env requires database url."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        ChatRagSettings.from_env()

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
_DEFAULT_MULTI_QUERY_COUNT = 3
_DEFAULT_CONTEXT_MAX_CHARS = 3500
_PARSED_MULTI_QUERY_COUNT = 2
_PARSED_CONTEXT_MAX_CHARS = 2048


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


def test_str_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """String env helper returns the configured value when set."""
    from vecinita_chat_rag_backend.config import (  # noqa: PLC0415
        _str_env,  # pyright: ignore[reportPrivateUsage]
    )

    monkeypatch.setenv("VECINITA_TEST_STR", "custom-model")
    assert _str_env("VECINITA_TEST_STR", "default-model") == "custom-model"


def test_from_env_defaults_f42_rag_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T92.1: F42 VECINITA_RAG_* defaults are H7 on, count=3, packer=p1."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_MULTI_QUERY", raising=False)
    monkeypatch.delenv("VECINITA_RAG_MULTI_QUERY_COUNT", raising=False)
    monkeypatch.delenv("VECINITA_RAG_PACKER", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CONTEXT_MAX_CHARS", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_multi_query is True
    assert settings.rag_multi_query_count == _DEFAULT_MULTI_QUERY_COUNT
    assert settings.rag_packer == "p1"
    assert settings.rag_context_max_chars == _DEFAULT_CONTEXT_MAX_CHARS


def test_from_env_parses_f42_rag_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T92.1: F42 VECINITA_RAG_* knobs parse from env (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_MULTI_QUERY", "false")
    monkeypatch.setenv("VECINITA_RAG_MULTI_QUERY_COUNT", "2")
    monkeypatch.setenv("VECINITA_RAG_PACKER", "p3")
    monkeypatch.setenv("VECINITA_RAG_CONTEXT_MAX_CHARS", "2048")
    settings = ChatRagSettings.from_env()
    assert settings.rag_multi_query is False
    assert settings.rag_multi_query_count == _PARSED_MULTI_QUERY_COUNT
    assert settings.rag_packer == "p3"
    assert settings.rag_context_max_chars == _PARSED_CONTEXT_MAX_CHARS


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("VECINITA_RAG_MULTI_QUERY_COUNT", "0"),
        ("VECINITA_RAG_MULTI_QUERY_COUNT", "6"),
        ("VECINITA_RAG_PACKER", "p2"),
        ("VECINITA_RAG_CONTEXT_MAX_CHARS", "100"),
    ],
)
def test_from_env_rejects_invalid_f42_rag_knobs(
    name: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T92.1: invalid VECINITA_RAG_* values raise at startup."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="VECINITA_RAG_"):
        ChatRagSettings.from_env()

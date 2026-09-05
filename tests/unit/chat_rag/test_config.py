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
_DEFAULT_TOP_K = 8
_DEFAULT_PACKER = "p3"
_ENV_MIN_SCORE = 0.3
_DEFAULT_MULTI_QUERY_COUNT = 3
_DEFAULT_CONTEXT_MAX_CHARS = 3500
_PARSED_MULTI_QUERY_COUNT = 2
_PARSED_CONTEXT_MAX_CHARS = 2048
_DEFAULT_CACHE_TTL_S = 3600
_DEFAULT_CACHE_MAX_ENTRIES = 1024
_DEFAULT_CACHE_SEMANTIC_THRESHOLD = 0.92
_PARSED_CACHE_TTL_S = 120
_PARSED_CACHE_MAX_ENTRIES = 64
_PARSED_CACHE_SEMANTIC_THRESHOLD = 0.95
_DEFAULT_CE_TOP_N = 20
_PARSED_CE_TOP_N = 15
_DEFAULT_CE_MODEL = "BAAI/bge-reranker-v2-m3"
_DEFAULT_REFINE_COUNT = 2
_PARSED_REFINE_COUNT = 3


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
    monkeypatch.delenv("VECINITA_FAQ_FASTPATH_ENABLED", raising=False)
    monkeypatch.delenv("VECINITA_FAQ_STORE_PATH", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.top_k == _ENV_TOP_K
    assert settings.min_retrieval_score == _ENV_MIN_SCORE
    assert settings.stats_enabled is False
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.faq_fastpath_enabled is True
    assert settings.faq_store_path is None


def test_from_env_parses_faq_fastpath_kill_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F85: VECINITA_FAQ_FASTPATH_ENABLED=0 and optional store path."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_FAQ_FASTPATH_ENABLED", "0")
    monkeypatch.setenv("VECINITA_FAQ_STORE_PATH", "/opt/vecinita/seed_faq.yaml")
    settings = ChatRagSettings.from_env()
    assert settings.faq_fastpath_enabled is False
    assert settings.faq_store_path == "/opt/vecinita/seed_faq.yaml"


def test_from_env_defaults_top_k_to_eight_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-193 / F50: ChatRAG top_k defaults to 8 when VECINITA_TOP_K is unset."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_TOP_K", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.top_k == _DEFAULT_TOP_K


def test_from_env_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test from env requires database url."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _ = ChatRagSettings.from_env()


def test_str_env_parses_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """String env helper returns the configured value when set."""
    from vecinita_chat_rag_backend.config import (  # noqa: PLC0415
        _str_env,  # pyright: ignore[reportPrivateUsage]
    )

    monkeypatch.setenv("VECINITA_TEST_STR", "custom-model")
    assert _str_env("VECINITA_TEST_STR", "default-model") == "custom-model"


def test_from_env_defaults_f42_rag_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T92.1: F42 VECINITA_RAG_* defaults are H7 on, count=3; packer default covered by TC-194."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_MULTI_QUERY", raising=False)
    monkeypatch.delenv("VECINITA_RAG_MULTI_QUERY_COUNT", raising=False)
    monkeypatch.delenv("VECINITA_RAG_PACKER", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CONTEXT_MAX_CHARS", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_multi_query is True
    assert settings.rag_multi_query_count == _DEFAULT_MULTI_QUERY_COUNT
    assert settings.rag_context_max_chars == _DEFAULT_CONTEXT_MAX_CHARS


def test_from_env_defaults_packer_to_p3_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-194 / F51: ChatRAG rag_packer defaults to p3 when VECINITA_RAG_PACKER unset."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_PACKER", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_packer == _DEFAULT_PACKER


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


def test_from_env_accepts_explicit_p1_packer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit VECINITA_RAG_PACKER=p1 parses (not only the default path)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_PACKER", "p1")
    settings = ChatRagSettings.from_env()
    assert settings.rag_packer == "p1"


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
        _ = ChatRagSettings.from_env()


def test_from_env_defaults_f43_rag_cache_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T95.1: F43 VECINITA_RAG_CACHE* defaults (config-spec / S020-D15)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_CACHE", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CACHE_TTL_S", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CACHE_MAX_ENTRIES", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CACHE_SEMANTIC", raising=False)
    monkeypatch.delenv("VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_cache is True
    assert settings.rag_cache_ttl_s == _DEFAULT_CACHE_TTL_S
    assert settings.rag_cache_max_entries == _DEFAULT_CACHE_MAX_ENTRIES
    assert settings.rag_cache_semantic is True
    assert settings.rag_cache_semantic_threshold == _DEFAULT_CACHE_SEMANTIC_THRESHOLD


def test_from_env_parses_f43_rag_cache_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T95.1: F43 VECINITA_RAG_CACHE* knobs parse from env (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_CACHE", "false")
    monkeypatch.setenv("VECINITA_RAG_CACHE_TTL_S", "120")
    monkeypatch.setenv("VECINITA_RAG_CACHE_MAX_ENTRIES", "64")
    monkeypatch.setenv("VECINITA_RAG_CACHE_SEMANTIC", "false")
    monkeypatch.setenv("VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD", "0.95")
    settings = ChatRagSettings.from_env()
    assert settings.rag_cache is False
    assert settings.rag_cache_ttl_s == _PARSED_CACHE_TTL_S
    assert settings.rag_cache_max_entries == _PARSED_CACHE_MAX_ENTRIES
    assert settings.rag_cache_semantic is False
    assert settings.rag_cache_semantic_threshold == _PARSED_CACHE_SEMANTIC_THRESHOLD


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("VECINITA_RAG_CACHE_TTL_S", "59"),
        ("VECINITA_RAG_CACHE_TTL_S", "86401"),
        ("VECINITA_RAG_CACHE_MAX_ENTRIES", "15"),
        ("VECINITA_RAG_CACHE_MAX_ENTRIES", "100001"),
        ("VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD", "0.49"),
        ("VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD", "1.01"),
    ],
)
def test_from_env_rejects_invalid_f43_rag_cache_knobs(
    name: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T95.1: invalid VECINITA_RAG_CACHE* values raise at startup."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="VECINITA_RAG_CACHE"):
        _ = ChatRagSettings.from_env()


def test_from_env_defaults_f44_soft_language_fallback_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-181 / AC-BB6: VECINITA_RAG_SOFT_LANGUAGE_FALLBACK defaults false (L0-strict)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_SOFT_LANGUAGE_FALLBACK", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_soft_language_fallback is False


def test_from_env_parses_f44_soft_language_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T96.2: VECINITA_RAG_SOFT_LANGUAGE_FALLBACK parses true/false (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_SOFT_LANGUAGE_FALLBACK", "true")
    settings = ChatRagSettings.from_env()
    assert settings.rag_soft_language_fallback is True
    monkeypatch.setenv("VECINITA_RAG_SOFT_LANGUAGE_FALLBACK", "false")
    settings = ChatRagSettings.from_env()
    assert settings.rag_soft_language_fallback is False


def test_from_env_defaults_f45_rerank_ce_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-183 / AC-BB8: VECINITA_RAG_RERANK_CE defaults false until ship gate."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_RERANK_CE", raising=False)
    monkeypatch.delenv("VECINITA_RAG_RERANK_CE_MODEL", raising=False)
    monkeypatch.delenv("VECINITA_RAG_RERANK_CE_TOP_N", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_rerank_ce is False
    assert settings.rag_rerank_ce_model == _DEFAULT_CE_MODEL
    assert settings.rag_rerank_ce_top_n == _DEFAULT_CE_TOP_N


def test_from_env_parses_f45_rerank_ce_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """T97.2: VECINITA_RAG_RERANK_CE* knobs parse from env (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_RERANK_CE", "true")
    monkeypatch.setenv("VECINITA_RAG_RERANK_CE_MODEL", _DEFAULT_CE_MODEL)
    monkeypatch.setenv("VECINITA_RAG_RERANK_CE_TOP_N", str(_PARSED_CE_TOP_N))
    monkeypatch.setenv("VECINITA_MODAL_RERANK_URL", "http://rerank.test")
    settings = ChatRagSettings.from_env()
    assert settings.rag_rerank_ce is True
    assert settings.rag_rerank_ce_model == _DEFAULT_CE_MODEL
    assert settings.rag_rerank_ce_top_n == _PARSED_CE_TOP_N


def test_from_env_rejects_invalid_f45_rerank_ce_top_n(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T97.2: VECINITA_RAG_RERANK_CE_TOP_N must be between top_k and 50."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_TOP_K", "5")
    monkeypatch.setenv("VECINITA_RAG_RERANK_CE_TOP_N", "3")
    with pytest.raises(ValueError, match="VECINITA_RAG_RERANK_CE_TOP_N"):
        _ = ChatRagSettings.from_env()


def test_from_env_defaults_f81_query_refine_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-283 / AC-SR5: VECINITA_RAG_QUERY_REFINE defaults false (F81)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_QUERY_REFINE", raising=False)
    monkeypatch.delenv("VECINITA_RAG_QUERY_REFINE_COUNT", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_query_refine is False
    assert settings.rag_query_refine_count == _DEFAULT_REFINE_COUNT


def test_from_env_parses_f81_query_refine_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """F81: VECINITA_RAG_QUERY_REFINE* knobs parse from env (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_QUERY_REFINE", "true")
    monkeypatch.setenv("VECINITA_RAG_QUERY_REFINE_COUNT", "3")
    settings = ChatRagSettings.from_env()
    assert settings.rag_query_refine is True
    assert settings.rag_query_refine_count == _PARSED_REFINE_COUNT


def test_from_env_defaults_f82_output_verify_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-286 / AC-OV4: VECINITA_RAG_OUTPUT_VERIFY defaults false (F82)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_RAG_OUTPUT_VERIFY", raising=False)
    monkeypatch.delenv("VECINITA_RAG_OUTPUT_VERIFY_MIN", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.rag_output_verify is False
    assert settings.rag_output_verify_min == 1.0


def test_from_env_parses_f82_output_verify_knobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """F82: VECINITA_RAG_OUTPUT_VERIFY* knobs parse from env (config-spec)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_OUTPUT_VERIFY", "true")
    monkeypatch.setenv("VECINITA_RAG_OUTPUT_VERIFY_MIN", "0.5")
    settings = ChatRagSettings.from_env()
    assert settings.rag_output_verify is True
    assert settings.rag_output_verify_min == _DEFAULT_FLOAT


def test_from_env_rejects_invalid_f82_output_verify_min(monkeypatch: pytest.MonkeyPatch) -> None:
    """F82: VECINITA_RAG_OUTPUT_VERIFY_MIN must stay within [0, 1]."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_OUTPUT_VERIFY_MIN", "1.5")
    with pytest.raises(ValueError, match="VECINITA_RAG_OUTPUT_VERIFY_MIN"):
        _ = ChatRagSettings.from_env()


def test_from_env_requires_rerank_url_when_ce_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """F45: VECINITA_MODAL_RERANK_URL required when VECINITA_RAG_RERANK_CE=true."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.setenv("VECINITA_RAG_RERANK_CE", "true")
    monkeypatch.delenv("VECINITA_MODAL_RERANK_URL", raising=False)
    with pytest.raises(ValueError, match="VECINITA_MODAL_RERANK_URL"):
        _ = ChatRagSettings.from_env()

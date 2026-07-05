"""Unit tests for ChatRAG production RAG config loader (ADR-035 §11)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import text
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.rag_production_config import (
    fallback_rag_config,
    load_active_rag_config,
)
from vecinita_shared_schemas.eval_config import EvalConfig

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.unit

_FALLBACK_TOP_K = 4
_ENV_TOP_K = 9
_DB_TOP_K = 11
_DEFAULT_MIN_SCORE = 0.2


@pytest.fixture
def chat_rag_settings(monkeypatch: pytest.MonkeyPatch) -> ChatRagSettings:
    """ChatRAG settings with distinct fallback values for loader tests."""
    monkeypatch.setenv("VECINITA_FALLBACK_TOP_K", str(_FALLBACK_TOP_K))
    monkeypatch.setenv("VECINITA_FALLBACK_MIN_RETRIEVAL_SCORE", str(_DEFAULT_MIN_SCORE))
    monkeypatch.setenv("VECINITA_FALLBACK_SYSTEM_PROMPT", "Fallback prompt")
    return ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        fallback_top_k=_FALLBACK_TOP_K,
        fallback_min_retrieval_score=_DEFAULT_MIN_SCORE,
        fallback_system_prompt="Fallback prompt",
    )


@pytest.fixture
def clean_rag_production_config(engine: Engine) -> Iterator[None]:
    """Remove production config rows before and after each test."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))


def test_fallback_rag_config_uses_settings_defaults(chat_rag_settings: ChatRagSettings) -> None:
    """Env fallback builder mirrors ChatRagSettings fallback fields."""
    config = fallback_rag_config(chat_rag_settings)
    assert config.top_k == _FALLBACK_TOP_K
    assert config.min_retrieval_score == _DEFAULT_MIN_SCORE
    assert config.system_prompt == "Fallback prompt"


def test_load_active_rag_config_returns_fallback_when_no_active_row(
    engine: Engine,
    chat_rag_settings: ChatRagSettings,
    clean_rag_production_config: None,
) -> None:
    """Missing active row falls back to env-derived EvalConfig."""
    _ = clean_rag_production_config
    loaded = load_active_rag_config(engine, chat_rag_settings)
    assert loaded.top_k == _FALLBACK_TOP_K
    assert loaded.system_prompt == "Fallback prompt"


def test_load_active_rag_config_reads_jsonb_dict_snapshot(
    engine: Engine,
    chat_rag_settings: ChatRagSettings,
    clean_rag_production_config: None,
) -> None:
    """Active DB row config dict overrides fallback values."""
    _ = clean_rag_production_config
    config = EvalConfig(
        top_k=_DB_TOP_K,
        min_retrieval_score=0.55,
        system_prompt="DB prompt",
        max_tokens=256,
        temperature=0.3,
        model_id="qwen2.5:1.5b-instruct",
    ).model_dump(mode="json")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO rag_production_config (
                    id, config, config_version, is_active, promoted_at, promoted_by
                )
                VALUES (
                    :id,
                    CAST(:config AS jsonb),
                    1,
                    true,
                    NOW(),
                    :promoted_by
                )
                """
            ),
            {
                "id": uuid4(),
                "config": json.dumps(config),
                "promoted_by": uuid4(),
            },
        )
    loaded = load_active_rag_config(engine, chat_rag_settings)
    assert loaded.top_k == _DB_TOP_K
    assert loaded.system_prompt == "DB prompt"


def test_load_active_rag_config_parses_json_string_config(
    engine: Engine,
    chat_rag_settings: ChatRagSettings,
    clean_rag_production_config: None,
) -> None:
    """Config stored as a JSON string is validated into EvalConfig."""
    _ = clean_rag_production_config
    config_json = json.dumps({"top_k": _ENV_TOP_K, "system_prompt": "String JSON prompt"})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO rag_production_config (
                    id, config, config_version, is_active, promoted_at, promoted_by
                )
                VALUES (
                    :id,
                    CAST(:config AS jsonb),
                    2,
                    true,
                    NOW(),
                    :promoted_by
                )
                """
            ),
            {
                "id": uuid4(),
                "config": config_json,
                "promoted_by": uuid4(),
            },
        )
    loaded = load_active_rag_config(engine, chat_rag_settings)
    assert loaded.top_k == _ENV_TOP_K
    assert loaded.system_prompt == "String JSON prompt"

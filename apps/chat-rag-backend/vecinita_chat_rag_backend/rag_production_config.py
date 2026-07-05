"""Load active production RAG config from DB with env fallback (ADR-035 §11)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import mapping_row, row_int
from vecinita_shared_schemas.eval_config import (
    EvalConfig,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from vecinita_chat_rag_backend.config import ChatRagSettings


def _config_from_json(value: object) -> EvalConfig:
    if isinstance(value, str):
        return EvalConfig.model_validate_json(value)
    if isinstance(value, dict):
        return EvalConfig.model_validate(value)
    return EvalConfig()


def fallback_rag_config(settings: ChatRagSettings) -> EvalConfig:
    """Build production config from env fallback vars (config-spec §Eval playground)."""
    return EvalConfig(
        top_k=settings.fallback_top_k,
        min_retrieval_score=settings.fallback_min_retrieval_score,
        system_prompt=settings.fallback_system_prompt,
        max_tokens=settings.fallback_max_tokens,
        temperature=settings.fallback_temperature,
        model_id=settings.fallback_model_id,
    )


def load_active_rag_config(engine: Engine, settings: ChatRagSettings) -> EvalConfig:
    """Read active production config from DB or fall back to env defaults."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT config, config_version
                    FROM rag_production_config
                    WHERE is_active = true
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        return fallback_rag_config(settings)
    mapped = mapping_row(row)
    _ = row_int(mapped, "config_version")
    return _config_from_json(mapped.get("config"))

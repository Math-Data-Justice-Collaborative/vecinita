"""Unit tests for EvalConfig validation bounds (ADR-035 §5, config-spec)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_MAX_TOKENS,
    DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
    DEFAULT_EVAL_MODEL_ID,
    DEFAULT_EVAL_SYSTEM_PROMPT,
    DEFAULT_EVAL_TEMPERATURE,
    DEFAULT_EVAL_TOP_K,
    DEFAULT_EVAL_JUDGE_TEMPERATURE,
    EvalConfig,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetUpdateRequest,
    RagConfigPromoteRequest,
)


def test_eval_config_defaults_match_config_spec() -> None:
    """Playground defaults match config-spec / ADR-035 form defaults."""
    config = EvalConfig()
    assert config.top_k == DEFAULT_EVAL_TOP_K
    assert config.min_retrieval_score == DEFAULT_EVAL_MIN_RETRIEVAL_SCORE
    assert config.system_prompt == DEFAULT_EVAL_SYSTEM_PROMPT
    assert config.max_tokens == DEFAULT_EVAL_MAX_TOKENS
    assert config.temperature == DEFAULT_EVAL_TEMPERATURE
    assert config.corpus_profile == "fixture"
    assert config.judge_temperature == DEFAULT_EVAL_JUDGE_TEMPERATURE
    assert config.model_id == DEFAULT_EVAL_MODEL_ID


def test_eval_config_rejects_top_k_below_minimum() -> None:
    """top_k must be >= 1."""
    with pytest.raises(ValidationError):
        EvalConfig(top_k=0)


def test_eval_config_rejects_top_k_above_maximum() -> None:
    """top_k must be <= 50."""
    with pytest.raises(ValidationError):
        EvalConfig(top_k=51)


def test_eval_config_rejects_empty_system_prompt() -> None:
    """System_prompt must be 1-8000 chars."""
    with pytest.raises(ValidationError):
        EvalConfig(system_prompt="")


def test_eval_config_rejects_temperature_above_maximum() -> None:
    """Temperature must be <= 2.0."""
    with pytest.raises(ValidationError):
        EvalConfig(temperature=2.1)


def test_eval_config_preset_create_requires_name() -> None:
    """Preset create body requires non-empty name."""
    with pytest.raises(ValidationError):
        EvalConfigPresetCreateRequest(name="", config=EvalConfig())


def test_eval_config_preset_update_allows_partial_fields() -> None:
    """Preset PATCH accepts optional fields only."""
    body = EvalConfigPresetUpdateRequest(shared=True)
    assert body.shared is True
    assert body.name is None
    assert body.config is None


def test_rag_config_promote_requires_preset_id_when_source_preset() -> None:
    """Promote from preset requires preset_id."""
    with pytest.raises(ValidationError):
        RagConfigPromoteRequest(source="preset")


def test_rag_config_promote_accepts_run_source() -> None:
    """Promote from completed run requires run_id."""
    run_id = uuid4()
    body = RagConfigPromoteRequest(source="run", run_id=run_id)
    assert body.run_id == run_id

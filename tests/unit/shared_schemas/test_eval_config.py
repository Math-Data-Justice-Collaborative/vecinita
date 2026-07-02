"""Unit tests for EvalConfig validation bounds (ADR-035 §5, config-spec)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_TOP_K,
    EvalConfig,
    EvalConfigPartial,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetUpdateRequest,
    RagConfigPromoteRequest,
    merge_eval_config,
)
from vecinita_shared_schemas.internal_write import EvalRunCreateRequest


def test_eval_config_defaults_match_config_spec() -> None:
    """Playground defaults match config-spec / ADR-035 form defaults."""
    from vecinita_shared_schemas.eval_config import (  # noqa: PLC0415
        DEFAULT_EVAL_JUDGE_TEMPERATURE,
        DEFAULT_EVAL_MAX_TOKENS,
        DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
        DEFAULT_EVAL_MODEL_ID,
        DEFAULT_EVAL_SYSTEM_PROMPT,
        DEFAULT_EVAL_TEMPERATURE,
    )

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


def test_merge_eval_config_applies_only_set_partial_fields() -> None:
    """Partial overrides preserve unset base fields from preset/base config."""
    from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MAX_TOKENS  # noqa: PLC0415

    base_top_k = 7
    override_top_k = 11
    base = EvalConfig(top_k=base_top_k, system_prompt="Preset sandbox prompt for eval runs.")
    merged = merge_eval_config(base, EvalConfigPartial(top_k=override_top_k))
    assert merged.top_k == override_top_k
    assert merged.system_prompt == "Preset sandbox prompt for eval runs."
    assert merged.max_tokens == DEFAULT_EVAL_MAX_TOKENS


def test_eval_run_create_request_requires_question_for_adhoc() -> None:
    """Ad-hoc eval runs require a question in the POST body."""
    with pytest.raises(ValidationError):
        EvalRunCreateRequest(mode="adhoc")

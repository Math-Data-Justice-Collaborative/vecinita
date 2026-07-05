"""Eval playground config models (ADR-035 §5, config-spec §Eval playground)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvalCorpusProfile = Literal["fixture", "staging"]
EvalRunMode = Literal["golden", "adhoc"]
RagConfigPromoteSource = Literal["preset", "run"]

MIN_EVAL_TOP_K = 1
MAX_EVAL_TOP_K = 50
MIN_EVAL_SYSTEM_PROMPT_LEN = 1
MAX_EVAL_SYSTEM_PROMPT_LEN = 8000
MIN_EVAL_MAX_TOKENS = 1
MAX_EVAL_MAX_TOKENS = 1024
MIN_EVAL_TEMPERATURE = 0.0
MAX_EVAL_TEMPERATURE = 2.0

DEFAULT_EVAL_TOP_K = 5
DEFAULT_EVAL_MIN_RETRIEVAL_SCORE = 0.2
DEFAULT_EVAL_MAX_TOKENS = 256
DEFAULT_EVAL_TEMPERATURE = 0.2
DEFAULT_EVAL_JUDGE_TEMPERATURE = 0.2
DEFAULT_EVAL_MODEL_ID = "qwen2.5:1.5b-instruct"

DEFAULT_EVAL_SYSTEM_PROMPT = (
    "Answer community questions using only the context below. Be concise. "
    "If the context does not answer the question, say you do not have that information."
)


class EvalConfigPartial(BaseModel):
    """Optional sandbox overrides for merge onto a base EvalConfig."""

    model_config = ConfigDict(extra="forbid")

    top_k: int | None = Field(default=None, ge=MIN_EVAL_TOP_K, le=MAX_EVAL_TOP_K)
    min_retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    system_prompt: str | None = Field(
        default=None,
        min_length=MIN_EVAL_SYSTEM_PROMPT_LEN,
        max_length=MAX_EVAL_SYSTEM_PROMPT_LEN,
    )
    max_tokens: int | None = Field(
        default=None,
        ge=MIN_EVAL_MAX_TOKENS,
        le=MAX_EVAL_MAX_TOKENS,
    )
    temperature: float | None = Field(
        default=None,
        ge=MIN_EVAL_TEMPERATURE,
        le=MAX_EVAL_TEMPERATURE,
    )
    corpus_profile: EvalCorpusProfile | None = None
    criteria_ids: list[UUID] | None = None
    judge_temperature: float | None = Field(
        default=None,
        ge=MIN_EVAL_TEMPERATURE,
        le=MAX_EVAL_TEMPERATURE,
    )
    model_id: str | None = Field(default=None, min_length=1, max_length=128)


class EvalConfig(BaseModel):
    """Sandbox RAG + judge overrides for eval runs and production promote."""

    model_config = ConfigDict(extra="forbid")

    top_k: int = Field(default=DEFAULT_EVAL_TOP_K, ge=MIN_EVAL_TOP_K, le=MAX_EVAL_TOP_K)
    min_retrieval_score: float = Field(
        default=DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
        ge=0.0,
        le=1.0,
    )
    system_prompt: str = Field(
        default=DEFAULT_EVAL_SYSTEM_PROMPT,
        min_length=MIN_EVAL_SYSTEM_PROMPT_LEN,
        max_length=MAX_EVAL_SYSTEM_PROMPT_LEN,
    )
    max_tokens: int = Field(
        default=DEFAULT_EVAL_MAX_TOKENS,
        ge=MIN_EVAL_MAX_TOKENS,
        le=MAX_EVAL_MAX_TOKENS,
    )
    temperature: float = Field(
        default=DEFAULT_EVAL_TEMPERATURE,
        ge=MIN_EVAL_TEMPERATURE,
        le=MAX_EVAL_TEMPERATURE,
    )
    corpus_profile: EvalCorpusProfile = "fixture"
    criteria_ids: list[UUID] = Field(default_factory=list)
    judge_temperature: float = Field(
        default=DEFAULT_EVAL_JUDGE_TEMPERATURE,
        ge=MIN_EVAL_TEMPERATURE,
        le=MAX_EVAL_TEMPERATURE,
    )
    model_id: str = Field(default=DEFAULT_EVAL_MODEL_ID, min_length=1, max_length=128)


def merge_eval_config(base: EvalConfig, partial: EvalConfigPartial | None) -> EvalConfig:
    """Apply only explicitly provided partial fields onto a base config."""
    if partial is None:
        return base
    updates = partial.model_dump(exclude_unset=True)
    return base.model_copy(update=updates)


class EvalConfigPresetCreateRequest(BaseModel):
    """POST /internal/v1/eval/config-presets body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    config: EvalConfig = Field(default_factory=EvalConfig)
    shared: bool = False


class EvalConfigPresetUpdateRequest(BaseModel):
    """PATCH /internal/v1/eval/config-presets/{preset_id} body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    config: EvalConfig | None = None
    shared: bool | None = None


class EvalConfigPresetResponse(BaseModel):
    """One saved eval config preset."""

    preset_id: UUID
    version: int
    name: str
    config: EvalConfig
    shared: bool
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class EvalConfigPresetListResponse(BaseModel):
    """GET /internal/v1/eval/config-presets response."""

    items: list[EvalConfigPresetResponse]


class EvalConfigPresetCloneRequest(BaseModel):
    """POST /internal/v1/eval/config-presets/{preset_id}/clone optional body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)


class RagConfigPromoteRequest(BaseModel):
    """POST /internal/v1/rag/config/promote body."""

    model_config = ConfigDict(extra="forbid")

    source: RagConfigPromoteSource
    preset_id: UUID | None = None
    run_id: UUID | None = None

    @model_validator(mode="after")
    def _require_source_id(self) -> RagConfigPromoteRequest:
        if self.source == "preset" and self.preset_id is None:
            msg = "preset_id is required when source is preset"
            raise ValueError(msg)
        if self.source == "run" and self.run_id is None:
            msg = "run_id is required when source is run"
            raise ValueError(msg)
        return self


class RagConfigPromoteResponse(BaseModel):
    """POST /internal/v1/rag/config/promote response."""

    config_version: int
    promoted_at: datetime
    promoted_by: UUID


class RagConfigActiveResponse(BaseModel):
    """GET /internal/v1/rag/config/active response."""

    config: EvalConfig
    config_version: int
    promoted_at: datetime | None = None
    promoted_by: UUID | None = None

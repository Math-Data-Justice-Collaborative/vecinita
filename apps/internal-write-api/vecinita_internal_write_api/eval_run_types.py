"""Eval run domain types and errors (F36)."""

from __future__ import annotations

from dataclasses import dataclass

from vecinita_shared_schemas.eval_config import EvalConfig, EvalRunMode
from vecinita_shared_schemas.internal_write import EvalRunCreateResponse


class EvalRunNotFoundError(LookupError):
    """Eval run id does not exist."""


@dataclass(frozen=True)
class LoadedEvalRun:
    """Eval run row fields needed by the background runner."""

    config_snapshot: EvalConfig
    mode: EvalRunMode
    corpus_profile: str


class EvalRunPresetNotFoundError(LookupError):
    """Referenced preset_id does not exist."""


class EvalRunPresetAccessError(PermissionError):
    """Caller cannot read the referenced preset."""


@dataclass(frozen=True)
class CreatedEvalRun:
    """Persisted eval run metadata for scheduling and API responses."""

    response: EvalRunCreateResponse
    corpus_profile: str
    mode: EvalRunMode
    question: str | None
    config_snapshot: EvalConfig

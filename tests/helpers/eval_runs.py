"""Helpers for creating eval runs in unit/integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from vecinita_internal_write_api.eval_service import CreatedEvalRun, create_eval_run
from vecinita_shared_schemas.internal_write import EvalRunCreateRequest

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from vecinita_shared_schemas.eval_config import EvalConfigPartial, EvalRunMode


def create_test_eval_run(  # noqa: PLR0913
    engine: Engine,
    *,
    corpus_profile: str = "fixture",
    mode: EvalRunMode = "golden",
    question: str | None = None,
    config: EvalConfigPartial | None = None,
    preset_id: UUID | None = None,
    requester_id: UUID | None = None,
) -> CreatedEvalRun:
    """Insert a pending eval run using the EV-009 create API shape."""
    return create_eval_run(
        engine,
        body=EvalRunCreateRequest(
            corpus_profile=corpus_profile,  # pyright: ignore[reportArgumentType]
            mode=mode,
            question=question,
            config=config,
            preset_id=preset_id,
        ),
        requester_id=requester_id or uuid4(),
    )

"""Eval and RAG config route registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vecinita_internal_write_api.eval_events import EvalRunEventBroker
from vecinita_internal_write_api.jobs_client import DataManagementJobsClient
from vecinita_internal_write_api.routes.eval_criteria import register_eval_criteria_routes
from vecinita_internal_write_api.routes.eval_presets import register_eval_preset_routes
from vecinita_internal_write_api.routes.eval_runs import register_eval_run_routes
from vecinita_internal_write_api.routes.rag_config import register_rag_config_routes

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI
    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


def register_eval_routes(  # noqa: PLR0913 — factory passes injectable eval clients and SSE knobs
    app: FastAPI,
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
    resolved_eval_embed: Callable[[str], list[float]] | None,
    resolved_eval_judge: JudgeClient | None,
    event_broker: EvalRunEventBroker,
    sse_poll_interval_s: float,
    sse_max_cycles: int | None,
    eval_sse_sync_db: bool,
) -> None:
    """Register eval run, criteria, config preset, and RAG config routes."""
    register_eval_run_routes(
        app,
        engine=engine,
        retag_jobs=retag_jobs,
        resolved_eval_embed=resolved_eval_embed,
        resolved_eval_judge=resolved_eval_judge,
        event_broker=event_broker,
        sse_poll_interval_s=sse_poll_interval_s,
        sse_max_cycles=sse_max_cycles,
        eval_sse_sync_db=eval_sse_sync_db,
    )
    register_eval_criteria_routes(app, engine=engine)
    register_eval_preset_routes(app, engine=engine)
    register_rag_config_routes(app, engine=engine)

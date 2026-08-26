"""Eval run persistence and background execution (F36, ADR-033; EV-009 T68.6)."""

from __future__ import annotations

from vecinita_internal_write_api.eval_run_crud import (
    create_eval_run,
    get_eval_run,
    get_eval_timeseries,
    list_eval_runs,
    resolve_eval_run_config,
    soft_delete_eval_run,
)
from vecinita_internal_write_api.eval_run_execute import execute_eval_run
from vecinita_internal_write_api.eval_run_types import (
    CreatedEvalRun,
    EvalRunNotFoundError,
    EvalRunPresetAccessError,
    EvalRunPresetNotFoundError,
    LoadedEvalRun,
)

__all__ = [
    "CreatedEvalRun",
    "EvalRunNotFoundError",
    "EvalRunPresetAccessError",
    "EvalRunPresetNotFoundError",
    "LoadedEvalRun",
    "create_eval_run",
    "execute_eval_run",
    "get_eval_run",
    "get_eval_timeseries",
    "list_eval_runs",
    "resolve_eval_run_config",
    "soft_delete_eval_run",
]

"""Corpus automations config and run routes (F75)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import FastAPI, Query, status
from vecinita_shared_schemas.automations import (
    AutomationRun,
    AutomationRunCreateRequest,
    AutomationRunListResponse,
    AutomationsConfigPatchRequest,
    AutomationsConfigResponse,
)

from vecinita_internal_write_api.automations import (
    create_automation_run,
    get_automations_config,
    list_automation_runs,
    set_automations_enabled,
)
from vecinita_internal_write_api.deps import WriteActorDep

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_automations_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register automations config and run history routes."""

    @app.get(
        "/internal/v1/automations/config",
        response_model=AutomationsConfigResponse,
    )
    def get_automations_config_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
    ) -> AutomationsConfigResponse:
        return get_automations_config(engine)

    @app.patch(
        "/internal/v1/automations/config",
        response_model=AutomationsConfigResponse,
    )
    def patch_automations_config_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
        body: AutomationsConfigPatchRequest,
    ) -> AutomationsConfigResponse:
        return set_automations_enabled(engine, enabled=body.enabled)

    @app.get(
        "/internal/v1/automations/runs",
        response_model=AutomationRunListResponse,
    )
    def list_automations_runs_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> AutomationRunListResponse:
        return list_automation_runs(engine, page=page, page_size=page_size)

    @app.post(
        "/internal/v1/automations/runs",
        response_model=AutomationRun,
        status_code=status.HTTP_201_CREATED,
    )
    def create_automations_run_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
        body: AutomationRunCreateRequest,
    ) -> AutomationRun:
        return create_automation_run(engine, body)

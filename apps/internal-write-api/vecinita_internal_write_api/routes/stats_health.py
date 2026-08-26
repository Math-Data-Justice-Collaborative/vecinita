"""Stats and aggregate health routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, status
from vecinita_shared_schemas.auth import require_authenticated
from vecinita_shared_schemas.internal_write import (
    HealthAggregateResponse,
    StatsServedRequest,
    StatsServedResponse,
    StatsSummaryResponse,
    TopServedResponse,
)

from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.health_service import aggregate_health
from vecinita_internal_write_api.stats_service import (
    fetch_stats_summary,
    fetch_top_served,
    record_documents_served,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_stats_health_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register stats summary/served/top-served and health/all routes."""

    @app.get(
        "/internal/v1/health/all",
        response_model=HealthAggregateResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def health_all() -> HealthAggregateResponse:  # pyright: ignore[reportUnusedFunction]
        return aggregate_health(engine=engine)

    @app.get(
        "/internal/v1/stats/summary",
        response_model=StatsSummaryResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def stats_summary() -> StatsSummaryResponse:  # pyright: ignore[reportUnusedFunction]
        return fetch_stats_summary(engine=engine)

    @app.post(
        "/internal/v1/stats/served",
        response_model=StatsServedResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def stats_served(body: StatsServedRequest, _actor: WriteActorDep) -> StatsServedResponse:  # pyright: ignore[reportUnusedFunction]
        return record_documents_served(engine=engine, body=body)

    @app.get(
        "/internal/v1/stats/top-served",
        response_model=TopServedResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def top_served(limit: int = 10) -> TopServedResponse:  # pyright: ignore[reportUnusedFunction]
        return fetch_top_served(engine=engine, limit=limit)

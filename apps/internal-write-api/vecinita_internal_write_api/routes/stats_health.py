"""Stats and aggregate health routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import Depends, FastAPI, status
from vecinita_shared_schemas.auth import require_authenticated
from vecinita_shared_schemas.internal_write import (
    HealthAggregateResponse,
    MetricsEventAccepted,
    MetricsEventRecord,
    MetricsEventRequest,
    MetricsSummaryResponse,
    MetricsTimeseriesResponse,
    StatsServedRequest,
    StatsServedResponse,
    StatsSummaryResponse,
    TopServedResponse,
)

from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.health_service import aggregate_health
from vecinita_internal_write_api.metrics_query import (
    fetch_metrics_summary,
    fetch_metrics_timeseries,
    parse_metrics_metric,
    parse_metrics_window,
)
from vecinita_internal_write_api.metrics_service import fetch_metric_event, record_metric_event
from vecinita_internal_write_api.stats_service import (
    fetch_stats_summary,
    fetch_top_served,
    record_documents_served,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_stats_health_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register stats summary/served/top-served, metrics events, and health/all routes."""

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

    @app.post(
        "/internal/v1/metrics/events",
        response_model=MetricsEventAccepted,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def metrics_events_create(  # pyright: ignore[reportUnusedFunction]
        body: MetricsEventRequest,
        _actor: WriteActorDep,
    ) -> MetricsEventAccepted:
        return record_metric_event(engine=engine, body=body)

    @app.get(
        "/internal/v1/metrics/events/{event_id}",
        response_model=MetricsEventRecord,
        dependencies=[Depends(require_authenticated)],
    )
    def metrics_events_get(event_id: UUID) -> MetricsEventRecord:  # pyright: ignore[reportUnusedFunction]
        return fetch_metric_event(engine=engine, event_id=event_id)

    @app.get(
        "/internal/v1/metrics/summary",
        response_model=MetricsSummaryResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def metrics_summary(window: str = "24h") -> MetricsSummaryResponse:  # pyright: ignore[reportUnusedFunction]
        return fetch_metrics_summary(engine=engine, window=parse_metrics_window(window))

    @app.get(
        "/internal/v1/metrics/timeseries",
        response_model=MetricsTimeseriesResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def metrics_timeseries(  # pyright: ignore[reportUnusedFunction]
        metric: str,
        window: str = "7d",
    ) -> MetricsTimeseriesResponse:
        return fetch_metrics_timeseries(
            engine=engine,
            metric=parse_metrics_metric(metric),
            window=parse_metrics_window(window),
        )

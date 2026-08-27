"""FastAPI internal write API — sole DATABASE_URL holder (ADR-007)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.internal_write import HealthResponse

from vecinita_internal_write_api.deps import (
    database_url as _database_url,  # noqa: F401  # pyright: ignore[reportUnusedImport]  # test import
)
from vecinita_internal_write_api.deps import (
    engine as _engine,
)
from vecinita_internal_write_api.deps import (
    row_datetime_optional as _row_datetime_optional,  # noqa: F401  # pyright: ignore[reportUnusedImport]  # test import
)
from vecinita_internal_write_api.eval_events import EvalRunEventBroker
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)
from vecinita_internal_write_api.playground_library_client import (
    PlaygroundLibraryClient,
    PlaygroundLibraryClientProtocol,
)
from vecinita_internal_write_api.routes.audit_feedback import register_audit_feedback_routes
from vecinita_internal_write_api.routes.automations import register_automations_routes
from vecinita_internal_write_api.routes.bulk import register_bulk_routes
from vecinita_internal_write_api.routes.documents import register_document_routes
from vecinita_internal_write_api.routes.eval import register_eval_routes
from vecinita_internal_write_api.routes.playground import register_playground_routes
from vecinita_internal_write_api.routes.rebuild import register_rebuild_routes
from vecinita_internal_write_api.routes.stats_health import register_stats_health_routes

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_eval.judges import JudgeClient

    from vecinita_internal_write_api.playground_service import LlmModelsClientProtocol


def _default_jobs_client() -> DataManagementJobsClient | None:
    """Auto-create a DataManagementJobsClient from env vars when available."""
    try:
        return DataManagementJobsClient()
    except DataManagementJobsClientError:
        return None


def _default_playground_models_client() -> LlmClient | None:
    """Auto-create an LlmClient for Modal list/pull from playground URL when available."""
    try:
        return LlmClient(require_proxy_key=True, purpose="playground")
    except LlmClientError:
        return None


def _default_playground_library_client() -> PlaygroundLibraryClient:
    """Auto-create the public playground library scraper."""
    return PlaygroundLibraryClient()


def create_app(  # noqa: PLR0913  # factory accepts injectable clients for tests
    *,
    jobs_client: DataManagementJobsClient | None = None,
    eval_embed_fn: Callable[[str], list[float]] | None = None,
    eval_judge: JudgeClient | None = None,
    playground_models_client: LlmModelsClientProtocol | None = None,
    playground_library_client: PlaygroundLibraryClientProtocol | None = None,
    eval_event_broker: EvalRunEventBroker | None = None,
    sse_poll_interval_s: float = 0.25,
    sse_max_cycles: int | None = None,
    eval_sse_sync_db: bool = True,
) -> FastAPI:
    """Build the internal write API (sole holder of DATABASE_URL)."""
    app = FastAPI(title="Vecinita Internal Write API", version="0.1.0")
    _ = configure_cors(app, extra_allow_headers=["Authorization"])
    engine = _engine()
    retag_jobs = jobs_client if jobs_client is not None else _default_jobs_client()
    resolved_eval_embed = eval_embed_fn
    resolved_eval_judge = eval_judge
    playground_models = (
        playground_models_client
        if playground_models_client is not None
        else _default_playground_models_client()
    )
    playground_library = (
        playground_library_client
        if playground_library_client is not None
        else _default_playground_library_client()
    )
    event_broker = eval_event_broker if eval_event_broker is not None else EvalRunEventBroker()

    register_bulk_routes(app, engine=engine, retag_jobs=retag_jobs)
    register_stats_health_routes(app, engine=engine)
    register_document_routes(app, engine=engine, retag_jobs=retag_jobs)
    register_rebuild_routes(app, engine=engine)
    register_audit_feedback_routes(app, engine=engine)
    register_automations_routes(app, engine=engine)
    register_eval_routes(
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
    register_playground_routes(
        app,
        playground_models=playground_models,
        playground_library=playground_library,
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:  # pyright: ignore[reportUnusedFunction]
        return HealthResponse(status="ok")

    return app

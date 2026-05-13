"""FastAPI application factory for the data-management API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_config import get_settings

from vecinita_dm_api.corpus_db_guard import validate_canonical_database_url
from vecinita_dm_api.routers import health, ingest, jobs_proxy


def create_app() -> FastAPI:
    settings = get_settings()
    validate_canonical_database_url(service_name="data-management-api")
    app = FastAPI(
        title="Vecinita Data Management API",
        description=(
            "Operator-facing API: scrape job paths proxy to the scraper service; "
            "/embed and /predict delegate to service-clients (Modal or HTTP)."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(jobs_proxy.router)
    app.include_router(ingest.router)
    return app

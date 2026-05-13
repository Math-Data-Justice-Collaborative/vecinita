"""Aggregate health via ``ScraperClient`` (Modal or HTTP per ``MODAL_FUNCTION_INVOCATION``)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from service_clients.scraper_client import ScraperClient, ScraperUpstreamError
from shared_config import get_settings
from vecinita_dm_api.corpus_db_guard import validate_canonical_database_url

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    try:
        validate_canonical_database_url(service_name="data-management-api-health")
        return await ScraperClient(get_settings().scraper_service_url).health()
    except ScraperUpstreamError as exc:
        raise HTTPException(
            status_code=exc.mapped_http_status or 503,
            detail=str(exc),
        ) from exc

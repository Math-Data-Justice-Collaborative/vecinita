"""Proxy operator scrape job HTTP to ``ScraperClient.forward_jobs`` (same paths as scraper OpenAPI)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse

from service_clients.scraper_client import ScraperClient, ScraperUpstreamError
from shared_config import get_settings

from vecinita_dm_api.routers.responses import httpx_to_starlette

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _forward_jobs(rest: str, request: Request):
    settings = get_settings()
    client = ScraperClient(settings.scraper_service_url)
    headers: dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    body: bytes | None = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
    try:
        upstream = await client.forward_jobs(
            request.method,
            rest,
            query=request.url.query,
            content=body if body else None,
            headers=headers or None,
        )
    except ScraperUpstreamError as exc:
        raise HTTPException(
            status_code=exc.mapped_http_status or 503,
            detail=str(exc),
        ) from exc
    if request.method == "POST":
        try:
            payload = upstream.json()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            payload.setdefault("source_of_truth", "postgres")
            payload.setdefault(
                "canonical_visibility_updated_at",
                datetime.now(timezone.utc).isoformat(),
            )
            return JSONResponse(status_code=upstream.status_code, content=payload)

    return httpx_to_starlette(upstream)


@router.api_route("", methods=["GET", "POST"])
async def jobs_collection(request: Request):
    return await _forward_jobs("", request)


@router.api_route("/{rest:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def jobs_under(rest: str, request: Request):
    return await _forward_jobs(rest, request)

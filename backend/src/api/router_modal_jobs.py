"""Gateway routes for Modal-native scraper job CRUD and tracked Modal calls."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.services.modal.invoker import (
    get_modal_function_call_result,
    invoke_modal_scrape_job_cancel,
    invoke_modal_scrape_job_get,
    invoke_modal_scrape_job_list,
    invoke_modal_scrape_job_submit,
    modal_function_invocation_enabled,
    spawn_modal_scraper_reindex,
)
from src.services.modal.job_registry import modal_job_registry

router = APIRouter(prefix="/modal-jobs", tags=["Modal jobs"])


def _require_modal_invocation() -> None:
    if not modal_function_invocation_enabled():
        raise HTTPException(
            status_code=503,
            detail="Modal function invocation is disabled. Set MODAL_FUNCTION_INVOCATION=auto|1 and Modal tokens.",
        )


def _unwrap_scraper_envelope(env: dict[str, Any]) -> dict[str, Any]:
    if env.get("ok"):
        data = env.get("data")
        return data if isinstance(data, dict) else {}
    status_code = int(env.get("http_status") or 500)
    detail = str(env.get("detail") or env.get("code") or "Modal scraper RPC error")
    raise HTTPException(status_code=status_code, detail=detail)


class GatewayModalScrapeSubmitRequest(BaseModel):
    """Body aligned with scraper ``ScrapeJobRequest`` (passed through to Modal)."""

    url: HttpUrl
    user_id: str = Field(..., min_length=1)
    crawl_config: dict[str, Any] | None = None
    chunking_config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.com/community-page",
                    "user_id": "live-test-user",
                    "crawl_config": None,
                    "chunking_config": None,
                    "metadata": {},
                },
                {
                    "url": "https://www.city.gov/housing/guide",
                    "user_id": "schemathesis",
                    "crawl_config": {},
                    "chunking_config": {},
                    "metadata": {"source": "openapi-example"},
                },
            ]
        }
    )


class GatewayModalReindexSpawnResponse(BaseModel):
    gateway_job_id: str
    modal_function_call_id: str
    modal_app: str
    modal_function: str
    message: str


@router.post("/scraper", summary="Submit scrape job via Modal function")
async def modal_scraper_submit(
    body: GatewayModalScrapeSubmitRequest,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> dict[str, Any]:
    payload = body.model_dump(mode="json")
    env = await asyncio.to_thread(invoke_modal_scrape_job_submit, payload)
    return _unwrap_scraper_envelope(env)


@router.get("/scraper/{job_id}", summary="Get scrape job status via Modal function")
async def modal_scraper_get(
    job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> dict[str, Any]:
    env = await asyncio.to_thread(invoke_modal_scrape_job_get, str(job_id))
    return _unwrap_scraper_envelope(env)


@router.get("/scraper", summary="List scrape jobs via Modal function")
async def modal_scraper_list(
    _: Annotated[None, Depends(_require_modal_invocation)],
    user_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    env = await asyncio.to_thread(invoke_modal_scrape_job_list, user_id, limit)
    data = _unwrap_scraper_envelope(env)
    jobs = data.get("jobs") or []
    fixed: list[dict[str, Any]] = []
    for row in jobs:
        if not isinstance(row, dict):
            continue
        r = dict(row)
        r.setdefault("job_id", str(r.get("id", "")))
        fixed.append(r)
    return {**data, "jobs": fixed}


@router.post("/scraper/{job_id}/cancel", summary="Cancel scrape job via Modal function")
async def modal_scraper_cancel(
    job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> dict[str, Any]:
    env = await asyncio.to_thread(invoke_modal_scrape_job_cancel, str(job_id))
    return _unwrap_scraper_envelope(env)


@router.post("/reindex/spawn", summary="Spawn reindex Modal function (non-blocking)")
async def modal_reindex_spawn(
    _: Annotated[None, Depends(_require_modal_invocation)],
    clean: bool = Query(default=False),
    stream: bool = Query(default=True),
    verbose: bool = Query(default=False),
) -> GatewayModalReindexSpawnResponse:
    import os

    call = await asyncio.to_thread(spawn_modal_scraper_reindex, clean, stream, verbose)
    call_id = str(getattr(call, "object_id", call))
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_REINDEX_FUNCTION", "trigger_reindex")
    gateway_job_id = await modal_job_registry.create_tracked_call(
        kind="reindex",
        function_call_id=call_id,
        app_name=app_name,
        function_name=fn_name,
        extra={"clean": clean, "stream": stream, "verbose": verbose},
    )
    return GatewayModalReindexSpawnResponse(
        gateway_job_id=gateway_job_id,
        modal_function_call_id=call_id,
        modal_app=app_name,
        modal_function=fn_name,
        message="Reindex spawned; poll GET /modal-jobs/registry/{gateway_job_id} for status.",
    )


@router.get("/registry", summary="List recent gateway-tracked Modal jobs")
async def modal_registry_list(
    _: Annotated[None, Depends(_require_modal_invocation)],
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    ids = await modal_job_registry.list_recent_ids(limit=limit)
    rows: list[dict[str, Any]] = []
    for jid in ids:
        rec = await modal_job_registry.get_record(jid)
        if rec:
            rows.append(rec)
    return {"jobs": rows, "total": len(rows)}


@router.get(
    "/registry/{gateway_job_id}", summary="Get tracked Modal job (optionally refresh result)"
)
async def modal_registry_get(
    gateway_job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
    refresh: bool = Query(
        default=False,
        description="If true, try a short Modal FunctionCall.get to move status to completed/failed.",
    ),
) -> dict[str, Any]:
    gid = str(gateway_job_id)
    rec = await modal_job_registry.get_record(gid)
    if not rec:
        raise HTTPException(status_code=404, detail="Unknown gateway_job_id")

    if refresh and rec.get("status") == "pending" and rec.get("modal_function_call_id"):
        call_id = str(rec["modal_function_call_id"])
        try:
            result = await asyncio.to_thread(get_modal_function_call_result, call_id, 0.05)
            await modal_job_registry.update_record(
                gid,
                {"status": "completed", "result": result, "error": None},
            )
            rec = await modal_job_registry.get_record(gid) or rec
        except TimeoutError:
            pass
        except Exception as exc:  # pragma: no cover - Modal runtime errors
            await modal_job_registry.update_record(
                gid,
                {"status": "failed", "error": str(exc), "result": None},
            )
            rec = await modal_job_registry.get_record(gid) or rec

    return rec


@router.delete("/registry/{gateway_job_id}", summary="Remove gateway-tracked Modal job metadata")
async def modal_registry_delete(
    gateway_job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> dict[str, Any]:
    gid = str(gateway_job_id)
    ok = await modal_job_registry.delete_record(gid)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown gateway_job_id")
    return {"gateway_job_id": gid, "deleted": True}

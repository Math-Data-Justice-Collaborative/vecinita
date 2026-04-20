"""Gateway routes for Modal-native scraper job CRUD and tracked Modal calls."""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from src.api.models import ErrorResponse, ValidationErrorResponse
from src.services.ingestion import modal_scraper_persist
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
from src.utils.database_url import get_resolved_database_url
from src.utils.gateway_dependency_errors import client_safe_message_for_dependency_failure

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modal-jobs", tags=["Modal jobs"])

# Matches ``http_exception_handler`` JSON in ``main.py`` (Schemathesis / TraceCov).
_GATEWAY_HTTP_ERROR_OPENAPI = {
    "application/json": {
        "schema": {
            "type": "object",
            "required": ["error", "timestamp"],
            "properties": {
                "error": {"type": "string"},
                "timestamp": {"type": "string"},
            },
        }
    }
}

# Malformed JSON reaches Starlette before Pydantic; response uses ``detail`` (not ``http_exception_handler`` shape).
_MALFORMED_JSON_BODY_OPENAPI = {
    "application/json": {
        "schema": {
            "type": "object",
            "required": ["detail"],
            "properties": {"detail": {"type": "string"}},
        }
    }
}

_MODAL_JOBS_VALIDATION = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Request validation failed (body, path, or query).",
    }
}

_MODAL_JOBS_SERVICE_UNAVAILABLE = {
    503: {
        "model": ErrorResponse,
        "description": "Modal invocation disabled or gateway persistence misconfigured.",
    }
}


def _gateway_owns_modal_scraper_control_plane() -> bool:
    return str(os.getenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _require_modal_invocation() -> None:
    if not modal_function_invocation_enabled():
        raise HTTPException(
            status_code=503,
            detail="Modal function invocation is disabled. Set MODAL_FUNCTION_INVOCATION=auto|1 and Modal tokens.",
        )


def _require_gateway_scrape_db_or_modal_invocation() -> None:
    """Status/list/cancel: gateway can serve from Postgres when persist-via-gateway is on.

    Otherwise callers need Modal SDK (``modal_scrape_job_get`` / list / cancel RPC).
    """
    if _gateway_owns_modal_scraper_control_plane():
        if not get_resolved_database_url().strip():
            raise HTTPException(
                status_code=503,
                detail="MODAL_SCRAPER_PERSIST_VIA_GATEWAY requires DATABASE_URL (or DB_URL) on the gateway",
            )
        return
    _require_modal_invocation()


def _unwrap_scraper_envelope(env: dict[str, Any]) -> dict[str, Any]:
    if env.get("ok"):
        data = env.get("data")
        return data if isinstance(data, dict) else {}
    status_code = int(env.get("http_status") or 500)
    detail = str(env.get("detail") or env.get("code") or "Modal scraper RPC error")
    if status_code >= 500:
        detail = client_safe_message_for_dependency_failure(RuntimeError(detail))
    raise HTTPException(status_code=status_code, detail=detail)


def _persist_runtime_http_detail(exc: RuntimeError) -> str:
    """FR-002-safe text for gateway-owned Postgres paths (belt-and-suspenders over persist layer)."""
    return client_safe_message_for_dependency_failure(exc)


def _submit_auto_kick_pipeline_enabled() -> bool:
    """After a successful Modal scrape submit, spawn ``trigger_reindex`` so drain workers run.

    Modal only enqueues to ``scrape-jobs``; ``trigger_reindex`` spawns the ``drain_*_queue``
    functions. Disable with ``MODAL_SCRAPER_SUBMIT_AUTO_KICK=0`` if you batch-kick separately.
    """
    raw = str(os.getenv("MODAL_SCRAPER_SUBMIT_AUTO_KICK", "1")).strip().lower()
    return raw not in {"0", "false", "no", "off"}


async def _kick_scraper_pipeline_after_submit() -> None:
    if not _submit_auto_kick_pipeline_enabled():
        return
    try:
        await asyncio.to_thread(spawn_modal_scraper_reindex, False, True, False)
    except Exception:
        logger.exception(
            "Modal trigger_reindex spawn failed after scrape submit; job may remain queued until "
            "POST /api/v1/scrape/reindex or POST /api/v1/modal-jobs/reindex/spawn"
        )


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


class GatewayModalScrapeJobBody(BaseModel):
    """Normalized Modal scraper job JSON (OpenAPI for Schemathesis stateful links)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    job_id: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("job_id", "id"),
        description="Scrape job id (Modal may return ``id`` or ``job_id``).",
    )
    status: str | None = Field(default=None, description="Job status when present.")


class GatewayModalScraperListResponse(BaseModel):
    """List envelope returned by ``GET /modal-jobs/scraper``."""

    model_config = ConfigDict(extra="allow")

    jobs: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class GatewayModalRegistryRecord(BaseModel):
    """Single gateway-tracked Modal job record."""

    model_config = ConfigDict(extra="allow")

    gateway_job_id: str = Field(..., min_length=1)
    kind: str | None = None
    status: str | None = None
    modal_function_call_id: str | None = None
    modal_app: str | None = None
    modal_function: str | None = None


class GatewayModalRegistryListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    jobs: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


_SCRAPER_SUBMIT_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalScrapeJobBody, "description": "Job accepted and queued."},
    400: {
        "description": "Request body is not valid JSON (parse error before validation).",
        "content": _MALFORMED_JSON_BODY_OPENAPI,
    },
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    500: {
        "description": "Modal RPC failure or Postgres error on the gateway.",
        "content": _GATEWAY_HTTP_ERROR_OPENAPI,
    },
}

_SCRAPER_GET_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalScrapeJobBody, "description": "Current job status."},
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    404: {"description": "Unknown job id.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
    500: {
        "description": "Modal RPC failure or Postgres error.",
        "content": _GATEWAY_HTTP_ERROR_OPENAPI,
    },
}

_SCRAPER_LIST_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalScraperListResponse, "description": "Recent jobs."},
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    500: {
        "description": "Modal RPC failure or Postgres error.",
        "content": _GATEWAY_HTTP_ERROR_OPENAPI,
    },
}

_SCRAPER_CANCEL_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalScrapeJobBody, "description": "Job cancelled or status returned."},
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    404: {"description": "Unknown job id.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
    409: {"description": "Job already terminal.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
    500: {
        "description": "Modal RPC failure or Postgres error.",
        "content": _GATEWAY_HTTP_ERROR_OPENAPI,
    },
}

_REGISTRY_RW_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalRegistryRecord, "description": "Registry record."},
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    404: {"description": "Unknown gateway_job_id.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
    500: {"description": "Unexpected failure.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
}

_REINDEX_SPAWN_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"model": GatewayModalReindexSpawnResponse, "description": "Spawn accepted."},
    **_MODAL_JOBS_VALIDATION,
    **_MODAL_JOBS_SERVICE_UNAVAILABLE,
    500: {"description": "Modal spawn failed.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
}


@router.post(
    "/scraper",
    summary="Submit scrape job via Modal function",
    response_model=GatewayModalScrapeJobBody,
    responses=_SCRAPER_SUBMIT_RESPONSES,
)
async def modal_scraper_submit(
    request: Request,
    body: GatewayModalScrapeSubmitRequest,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> GatewayModalScrapeJobBody:
    cid = getattr(request.state, "correlation_id", None)
    merged_metadata: dict[str, Any] = dict(body.metadata or {})
    if cid:
        merged_metadata["correlation_id"] = cid

    if _gateway_owns_modal_scraper_control_plane():
        if not get_resolved_database_url().strip():
            raise HTTPException(
                status_code=503,
                detail="MODAL_SCRAPER_PERSIST_VIA_GATEWAY requires DATABASE_URL (or DB_URL) on the gateway",
            )
        crawl = body.crawl_config or {}
        chunk = body.chunking_config or {}
        try:
            jid = await asyncio.to_thread(
                partial(
                    modal_scraper_persist.create_scraping_job,
                    url=str(body.url),
                    user_id=body.user_id,
                    crawl_config=crawl,
                    chunking_config=chunk,
                    metadata=merged_metadata,
                ),
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=_persist_runtime_http_detail(exc)) from exc
        payload = body.model_dump(mode="json")
        payload["metadata"] = merged_metadata
        payload["job_id"] = jid
        env = await asyncio.to_thread(invoke_modal_scrape_job_submit, payload)
        data = _unwrap_scraper_envelope(env)
        await _kick_scraper_pipeline_after_submit()
        return GatewayModalScrapeJobBody.model_validate(data)

    payload = body.model_dump(mode="json")
    payload["metadata"] = merged_metadata
    env = await asyncio.to_thread(invoke_modal_scrape_job_submit, payload)
    data = _unwrap_scraper_envelope(env)
    await _kick_scraper_pipeline_after_submit()
    return GatewayModalScrapeJobBody.model_validate(data)


@router.get(
    "/scraper/{job_id}",
    summary="Get scrape job status via Modal function",
    response_model=GatewayModalScrapeJobBody,
    responses=_SCRAPER_GET_RESPONSES,
)
async def modal_scraper_get(
    job_id: UUID,
    _: Annotated[None, Depends(_require_gateway_scrape_db_or_modal_invocation)],
) -> GatewayModalScrapeJobBody:
    if _gateway_owns_modal_scraper_control_plane():
        try:
            data = await asyncio.to_thread(modal_scraper_persist.job_status_payload, str(job_id))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=_persist_runtime_http_detail(exc)) from exc
        if not data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return GatewayModalScrapeJobBody.model_validate(data)

    env = await asyncio.to_thread(invoke_modal_scrape_job_get, str(job_id))
    data = _unwrap_scraper_envelope(env)
    return GatewayModalScrapeJobBody.model_validate(data)


@router.get(
    "/scraper",
    summary="List scrape jobs via Modal function",
    response_model=GatewayModalScraperListResponse,
    responses=_SCRAPER_LIST_RESPONSES,
)
async def modal_scraper_list(
    _: Annotated[None, Depends(_require_gateway_scrape_db_or_modal_invocation)],
    user_id: Annotated[str | None, Query(min_length=1)] = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> GatewayModalScraperListResponse:
    if _gateway_owns_modal_scraper_control_plane():
        try:
            data = await asyncio.to_thread(
                partial(modal_scraper_persist.list_jobs_payload, user_id=user_id, limit=limit),
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=_persist_runtime_http_detail(exc)) from exc
    else:
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
    return GatewayModalScraperListResponse(jobs=fixed, total=int(data.get("total") or len(fixed)))


@router.post(
    "/scraper/{job_id}/cancel",
    summary="Cancel scrape job via Modal function",
    response_model=GatewayModalScrapeJobBody,
    responses=_SCRAPER_CANCEL_RESPONSES,
)
async def modal_scraper_cancel(
    job_id: UUID,
    _: Annotated[None, Depends(_require_gateway_scrape_db_or_modal_invocation)],
) -> GatewayModalScrapeJobBody:
    if _gateway_owns_modal_scraper_control_plane():
        try:
            payload, err = await asyncio.to_thread(modal_scraper_persist.cancel_job, str(job_id))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=_persist_runtime_http_detail(exc)) from exc
        if err == "not_found":
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        if err == "conflict":
            raise HTTPException(
                status_code=409,
                detail="Job cannot be cancelled (already completed, failed, or cancelled)",
            )
        assert payload is not None
        return GatewayModalScrapeJobBody.model_validate(payload)

    env = await asyncio.to_thread(invoke_modal_scrape_job_cancel, str(job_id))
    data = _unwrap_scraper_envelope(env)
    return GatewayModalScrapeJobBody.model_validate(data)


@router.post(
    "/reindex/spawn",
    summary="Spawn reindex Modal function (non-blocking)",
    response_model=GatewayModalReindexSpawnResponse,
    responses=_REINDEX_SPAWN_RESPONSES,
)
async def modal_reindex_spawn(
    _: Annotated[None, Depends(_require_modal_invocation)],
    clean: bool = Query(default=False),
    stream: bool = Query(default=True),
    verbose: bool = Query(default=False),
) -> GatewayModalReindexSpawnResponse:
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


@router.get(
    "/registry",
    summary="List recent gateway-tracked Modal jobs",
    response_model=GatewayModalRegistryListResponse,
    responses={
        200: {"model": GatewayModalRegistryListResponse, "description": "Registry list."},
        **_MODAL_JOBS_VALIDATION,
        **_MODAL_JOBS_SERVICE_UNAVAILABLE,
        500: {"description": "Unexpected failure.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
    },
)
async def modal_registry_list(
    _: Annotated[None, Depends(_require_modal_invocation)],
    limit: int = Query(default=50, ge=1, le=100),
) -> GatewayModalRegistryListResponse:
    ids = await modal_job_registry.list_recent_ids(limit=limit)
    rows: list[dict[str, Any]] = []
    for jid in ids:
        rec = await modal_job_registry.get_record(jid)
        if rec:
            rows.append(rec)
    return GatewayModalRegistryListResponse(jobs=rows, total=len(rows))


@router.get(
    "/registry/{gateway_job_id}",
    summary="Get tracked Modal job (optionally refresh result)",
    response_model=GatewayModalRegistryRecord,
    responses=_REGISTRY_RW_RESPONSES,
)
async def modal_registry_get(
    gateway_job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
    refresh: bool = Query(
        default=False,
        description="If true, try a short Modal FunctionCall.get to move status to completed/failed.",
    ),
) -> GatewayModalRegistryRecord:
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

    return GatewayModalRegistryRecord.model_validate(rec)


@router.delete(
    "/registry/{gateway_job_id}",
    summary="Remove gateway-tracked Modal job metadata",
    responses={
        **_MODAL_JOBS_VALIDATION,
        **_MODAL_JOBS_SERVICE_UNAVAILABLE,
        404: {"description": "Unknown gateway_job_id.", "content": _GATEWAY_HTTP_ERROR_OPENAPI},
        200: {
            "description": "Deletion acknowledged.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "gateway_job_id": {"type": "string"},
                            "deleted": {"type": "boolean"},
                        },
                    }
                }
            },
        },
    },
)
async def modal_registry_delete(
    gateway_job_id: UUID,
    _: Annotated[None, Depends(_require_modal_invocation)],
) -> dict[str, Any]:
    gid = str(gateway_job_id)
    ok = await modal_job_registry.delete_record(gid)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown gateway_job_id")
    return {"gateway_job_id": gid, "deleted": True}

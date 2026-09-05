"""ChatRAG FastAPI backend (F1, F2, F3)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, cast
from uuid import UUID

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import text
from vecinita_shared_schemas.chat_rag import (
    AskRequest,
    AskResponse,
    DocumentBrowseDetail,
    DocumentBrowsePage,
    EnergyEstimate,
    FeedbackCreateResponse,
    HealthResponse,
    Source,
    TagListResponse,
)
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.validation import validate_ask_request, validate_feedback_request

from vecinita_chat_rag_backend.browse import get_document, list_documents, list_tag_facets
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.db import create_app_engine
from vecinita_chat_rag_backend.energy import EnergyKnobs, compute_energy_estimate
from vecinita_chat_rag_backend.service import ChatRagService

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine


async def parse_ask_body(request: Request) -> AskRequest:
    """Parse JSON ask body and reject identity fields per ADR-004."""
    try:
        raw_payload = cast("object", await request.json())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc
    if not isinstance(raw_payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON object required")
    payload = as_json_object(cast("object", raw_payload))
    try:
        return validate_ask_request(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc


def _check_dependency(url: str | None, path: str = "/health") -> str:
    if not url:
        return "not_configured"
    try:
        response = httpx.get(f"{url.rstrip('/')}{path}", timeout=5.0)
    except httpx.HTTPError:
        return "error"
    else:
        return "ok" if response.status_code == HTTPStatus.OK else "error"


def _warm_modal_url(
    url: str,
    *,
    timeout_s: float,
    headers: dict[str, str] | None = None,
) -> None:
    """Best-effort POST /warm on one Modal app; failures are ignored (S001 T11)."""
    with contextlib.suppress(Exception):
        _ = httpx.post(
            f"{url.rstrip('/')}/warm",
            timeout=timeout_s,
            headers=headers or {},
        )


def _warm_modal_services(
    embed_url: str | None,
    llm_url: str | None,
    *,
    request_timeout_s: float,
    llm_proxy_key: str | None = None,
) -> None:
    """Boot Modal EmbeddingService and LlmService in parallel during user think-time."""
    llm_headers: dict[str, str] | None = None
    if llm_proxy_key:
        # RD-165 — vecinita-llm /warm requires X-Vecinita-Proxy-Key (BUG-2026-08-27).
        llm_headers = {"X-Vecinita-Proxy-Key": llm_proxy_key}
    with ThreadPoolExecutor(max_workers=2) as executor:
        if embed_url:
            _ = executor.submit(_warm_modal_url, embed_url, timeout_s=request_timeout_s)
        if llm_url:
            _ = executor.submit(
                _warm_modal_url,
                llm_url,
                timeout_s=request_timeout_s,
                headers=llm_headers,
            )


def _source_payload(sources: list[Source]) -> list[dict[str, object]]:
    encoded: list[dict[str, object]] = []
    for source in sources:
        item = as_json_object(cast("object", jsonable_encoder(source)))
        for key in ("chunk_id", "document_id"):
            field = item.get(key)
            if isinstance(field, UUID):
                item[key] = str(field)
        encoded.append(item)
    return encoded


def _fire_stats(
    sources: list[Source],
    internal_write_url: str | None,
    internal_api_key: str | None,
    *,
    stats_enabled: bool = True,
) -> None:
    """Fire-and-forget POST to /stats/served. Failures are silently ignored."""
    if not stats_enabled or not internal_write_url or not sources:
        return
    doc_ids = list({str(s.document_id) for s in sources if s.document_id})
    if not doc_ids:
        return
    headers: dict[str, str] = {}
    if internal_api_key:
        headers["Authorization"] = f"Bearer {internal_api_key}"
    with contextlib.suppress(Exception):
        _ = httpx.post(
            f"{internal_write_url.rstrip('/')}/internal/v1/stats/served",
            json={"document_ids": doc_ids},
            headers=headers,
            timeout=5.0,
        )


def _fire_chat_metric(  # noqa: PLR0913  # fire-and-forget needs URL/key/outcome fields
    *,
    latency_ms: int,
    sources: list[Source],
    locale: str | None,
    internal_write_url: str | None,
    internal_api_key: str | None,
    metrics_enabled: bool = True,
    outcome: str = "success",
    error_code: str | None = None,
) -> None:
    """Fire-and-forget privacy-safe chat outcome event (F84). Never sends question/answer."""
    if not metrics_enabled or not internal_write_url:
        return
    resolved_outcome = outcome
    if outcome == "success" and not sources:
        resolved_outcome = "no_context"
    headers: dict[str, str] = {}
    if internal_api_key:
        headers["Authorization"] = f"Bearer {internal_api_key}"
    payload: dict[str, object] = {
        "workload": "chat",
        "outcome": resolved_outcome,
        "latency_ms": max(0, latency_ms),
        "error_code": error_code,
        "locale": locale,
    }
    with contextlib.suppress(Exception):
        _ = httpx.post(
            f"{internal_write_url.rstrip('/')}/internal/v1/metrics/events",
            json=payload,
            headers=headers,
            timeout=5.0,
        )


def create_app(  # noqa: C901, PLR0915  # FastAPI factory registers many route handlers inline
    *,
    settings: ChatRagSettings | None = None,
    chat_service: ChatRagService | None = None,
) -> FastAPI:
    """Build the ChatRAG FastAPI app with health, ask, and streaming routes."""
    app = FastAPI(title="Vecinita ChatRAG", version="0.2.0")
    _ = configure_cors(app)
    resolved_settings = settings
    resolved_service = chat_service
    resolved_engine: Engine | None = None

    def get_settings() -> ChatRagSettings:
        nonlocal resolved_settings
        if resolved_settings is None:
            resolved_settings = ChatRagSettings.from_env()
        return resolved_settings

    def get_engine() -> Engine:
        """One capped QueuePool for health + browse (DO max_connections=25)."""
        nonlocal resolved_engine
        if resolved_engine is None:
            resolved_engine = create_app_engine(
                get_settings().database_url,
                application_name="vecinita-chatrag",
            )
        return resolved_engine

    def get_service() -> ChatRagService:
        nonlocal resolved_service
        if resolved_service is None:
            resolved_service = ChatRagService.from_settings(get_settings())
        return resolved_service

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:  # pyright: ignore[reportUnusedFunction]  # FastAPI route
        cfg = get_settings()
        deps = {
            "postgres": "error",
            "modal_embed": _check_dependency(cfg.embed_url),
            "modal_llm": _check_dependency(cfg.llm_url),
        }
        try:
            with get_engine().connect() as conn:
                _ = conn.execute(text("SELECT 1"))
            deps["postgres"] = "ok"
        except Exception:  # noqa: BLE001  # health probe must tolerate any DB failure
            deps["postgres"] = "error"
        return HealthResponse(status="ok", dependencies=deps)

    @app.post("/api/v1/warm")
    def warm_modal(background_tasks: BackgroundTasks) -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        """Fire-and-forget Modal pre-warm when the chat UI mounts (S001 T11)."""
        cfg = get_settings()
        background_tasks.add_task(
            _warm_modal_services,
            cfg.embed_url,
            cfg.llm_url,
            request_timeout_s=cfg.request_timeout_s,
            llm_proxy_key=os.environ.get("VECINITA_MODAL_PROXY_KEY"),
        )
        return {"status": "warming"}

    def _energy_for_duration(duration_s: float, cfg: ChatRagSettings) -> EnergyEstimate:
        # Floor tiny durations so cache/fast paths still emit a positive estimate.
        wall_s = max(duration_s, 1e-3)
        return compute_energy_estimate(
            wall_s,
            EnergyKnobs(
                gpu_tdp_w=cfg.energy_gpu_tdp_w,
                gpu_util=cfg.energy_gpu_util,
                gco2e_per_kwh=cfg.energy_gco2e_per_kwh,
                car_gco2e_per_km=cfg.energy_car_gco2e_per_km,
            ),
        )

    @app.post("/api/v1/ask", response_model=AskResponse)
    async def ask(request: Request) -> AskResponse:  # pyright: ignore[reportUnusedFunction]
        body = await parse_ask_body(request)
        cfg = get_settings()
        started = time.perf_counter()
        try:
            # Offload sync RAG/LLM httpx work so DO /health probes keep running
            # (BUG-2026-08-05 — event-loop stall → 504 no_healthy_upstream).
            result = await asyncio.to_thread(get_service().ask, body)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Upstream unavailable",
            ) from exc
        estimate = _energy_for_duration(time.perf_counter() - started, cfg)
        latency_ms = int((time.perf_counter() - started) * 1000)
        _fire_stats(
            result.sources,
            cfg.internal_write_url,
            cfg.internal_api_key,
            stats_enabled=cfg.stats_enabled,
        )
        _fire_chat_metric(
            latency_ms=latency_ms,
            sources=result.sources,
            locale=result.language,
            internal_write_url=cfg.internal_write_url,
            internal_api_key=cfg.internal_api_key,
            metrics_enabled=cfg.metrics_enabled,
        )
        return result.model_copy(update={"energy_estimate": estimate})

    @app.post("/api/v1/ask/stream")
    async def ask_stream(request: Request) -> StreamingResponse:  # pyright: ignore[reportUnusedFunction]
        body = await parse_ask_body(request)
        cfg = get_settings()
        started = time.perf_counter()
        try:
            service = get_service()
            # stream_ask does sync retrieve/embed before yielding tokens — same stall risk.
            session = await asyncio.to_thread(service.stream_ask, body)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Upstream unavailable",
            ) from exc

        def event_stream() -> Iterator[str]:
            for token in session.tokens:
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'sources': _source_payload(session.sources)})}\n\n"
            estimate = _energy_for_duration(time.perf_counter() - started, cfg)
            done_payload = {
                "done": True,
                "cache_hit": session.cache_hit,
                "answer_path": session.answer_path,
                "energy_estimate": estimate.model_dump(mode="json"),
            }
            yield f"data: {json.dumps(done_payload)}\n\n"
            _fire_stats(
                session.sources,
                cfg.internal_write_url,
                cfg.internal_api_key,
                stats_enabled=cfg.stats_enabled,
            )
            _fire_chat_metric(
                latency_ms=int((time.perf_counter() - started) * 1000),
                sources=session.sources,
                locale=body.language,
                internal_write_url=cfg.internal_write_url,
                internal_api_key=cfg.internal_api_key,
                metrics_enabled=cfg.metrics_enabled,
            )

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/api/v1/documents", response_model=DocumentBrowsePage)
    def list_documents_public(  # pyright: ignore[reportUnusedFunction]
        tags: Annotated[list[str] | None, Query()] = None,
        q: Annotated[str | None, Query()] = None,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
    ) -> DocumentBrowsePage:
        cfg = get_settings()
        resolved_page_size = page_size or cfg.browse_page_size
        return list_documents(
            get_engine(),
            tags=tags,
            q=q,
            page=page,
            page_size=resolved_page_size,
        )

    @app.get("/api/v1/documents/{document_id}", response_model=DocumentBrowseDetail)
    def get_document_public(document_id: UUID) -> DocumentBrowseDetail:  # pyright: ignore[reportUnusedFunction]
        detail = get_document(get_engine(), document_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return detail

    @app.get("/api/v1/tags", response_model=TagListResponse)
    def list_tags_public() -> TagListResponse:  # pyright: ignore[reportUnusedFunction]
        return list_tag_facets(get_engine())

    @app.post(
        "/api/v1/feedback",
        response_model=FeedbackCreateResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def submit_feedback(request: Request) -> FeedbackCreateResponse:  # pyright: ignore[reportUnusedFunction]
        try:
            raw_payload = cast("object", await request.json())
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON",
            ) from exc
        if not isinstance(raw_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON object required",
            )
        try:
            body = validate_feedback_request(as_json_object(cast("object", raw_payload)))
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.errors(),
            ) from exc

        cfg = get_settings()
        if not cfg.internal_write_url or not cfg.internal_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Feedback write path unavailable",
            )
        try:
            async with httpx.AsyncClient(timeout=cfg.request_timeout_s) as client:
                response = await client.post(
                    f"{cfg.internal_write_url.rstrip('/')}/internal/v1/feedback",
                    json=body.model_dump(mode="json"),
                    headers={"Authorization": f"Bearer {cfg.internal_api_key}"},
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Feedback write path unavailable",
            ) from exc
        if response.status_code == HTTPStatus.BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.json(),
            )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Feedback write path unavailable",
            )
        return FeedbackCreateResponse.model_validate(response.json())

    return app

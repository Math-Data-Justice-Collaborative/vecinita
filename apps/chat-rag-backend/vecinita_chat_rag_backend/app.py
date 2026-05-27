"""ChatRAG FastAPI backend (F1, F2, F3)."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from typing import Annotated, cast
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.chat_rag import (
    AskRequest,
    AskResponse,
    DocumentBrowseDetail,
    DocumentBrowsePage,
    HealthResponse,
    Source,
    TagListResponse,
)
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.validation import validate_ask_request

from vecinita_chat_rag_backend.browse import get_document, list_documents, list_tag_facets
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService


async def parse_ask_body(request: Request) -> AskRequest:
    """Parse JSON ask body and reject identity fields per ADR-004."""
    try:
        raw_payload = cast(object, await request.json())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc
    if not isinstance(raw_payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON object required")
    payload = as_json_object(raw_payload)
    try:
        return validate_ask_request(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc


def _check_dependency(url: str | None, path: str = "/health") -> str:
    if not url:
        return "not_configured"
    try:
        response = httpx.get(f"{url.rstrip('/')}{path}", timeout=5.0)
        return "ok" if response.status_code == 200 else "error"
    except httpx.HTTPError:
        return "error"


def _source_payload(sources: list[Source]) -> list[dict[str, object]]:
    encoded: list[dict[str, object]] = []
    for source in sources:
        item = as_json_object(cast(object, jsonable_encoder(source)))
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
        httpx.post(
            f"{internal_write_url.rstrip('/')}/internal/v1/stats/served",
            json={"document_ids": doc_ids},
            headers=headers,
            timeout=5.0,
        )


def create_app(
    *,
    settings: ChatRagSettings | None = None,
    chat_service: ChatRagService | None = None,
) -> FastAPI:
    """Build the ChatRAG FastAPI app with health, ask, and streaming routes."""
    app = FastAPI(title="Vecinita ChatRAG", version="0.2.0")
    configure_cors(app)
    resolved_settings = settings
    resolved_service = chat_service

    def get_settings() -> ChatRagSettings:
        nonlocal resolved_settings
        if resolved_settings is None:
            resolved_settings = ChatRagSettings.from_env()
        return resolved_settings

    def get_service() -> ChatRagService:
        nonlocal resolved_service
        if resolved_service is None:
            resolved_service = ChatRagService.from_settings(get_settings())
        return resolved_service

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        cfg = get_settings()
        deps = {
            "postgres": "error",
            "modal_embed": _check_dependency(cfg.embed_url),
            "modal_llm": _check_dependency(cfg.llm_url),
        }
        try:
            engine = create_engine(cfg.database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            deps["postgres"] = "ok"
        except Exception:
            deps["postgres"] = "error"
        return HealthResponse(status="ok", dependencies=deps)

    @app.post("/api/v1/ask", response_model=AskResponse)
    async def ask(request: Request) -> AskResponse:
        body = await parse_ask_body(request)
        try:
            result = get_service().ask(body)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Upstream unavailable",
            ) from exc
        cfg = get_settings()
        _fire_stats(
            result.sources,
            cfg.internal_write_url,
            cfg.internal_api_key,
            stats_enabled=cfg.stats_enabled,
        )
        return result

    @app.post("/api/v1/ask/stream")
    async def ask_stream(request: Request) -> StreamingResponse:
        body = await parse_ask_body(request)
        try:
            service = get_service()
            sources = service.retrieve_sources(body)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Upstream unavailable",
            ) from exc

        def event_stream() -> Iterator[str]:
            if not sources:
                result = service.ask(body)
                yield f"data: {json.dumps({'token': result.answer})}\n\n"
                yield f"data: {json.dumps({'sources': []})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
                return
            for token in service.ask_stream(body):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'sources': _source_payload(sources)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/api/v1/documents", response_model=DocumentBrowsePage)
    def list_documents_public(
        tags: Annotated[list[str] | None, Query()] = None,
        q: Annotated[str | None, Query()] = None,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int | None, Query(ge=1, le=100)] = None,
    ) -> DocumentBrowsePage:
        cfg = get_settings()
        resolved_page_size = page_size or cfg.browse_page_size
        engine = create_engine(cfg.database_url)
        return list_documents(
            engine,
            tags=tags,
            q=q,
            page=page,
            page_size=resolved_page_size,
        )

    @app.get("/api/v1/documents/{document_id}", response_model=DocumentBrowseDetail)
    def get_document_public(document_id: UUID) -> DocumentBrowseDetail:
        cfg = get_settings()
        engine = create_engine(cfg.database_url)
        detail = get_document(engine, document_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return detail

    @app.get("/api/v1/tags", response_model=TagListResponse)
    def list_tags_public() -> TagListResponse:
        cfg = get_settings()
        engine = create_engine(cfg.database_url)
        return list_tag_facets(engine)

    return app

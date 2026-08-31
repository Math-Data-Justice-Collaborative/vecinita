"""Audit log and feedback routes."""

from __future__ import annotations

import json
import os
import uuid as _uuid
from typing import TYPE_CHECKING, Annotated, cast
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from pydantic import ValidationError
from vecinita_shared_schemas.auth import require_authenticated, require_service
from vecinita_shared_schemas.chat_rag import FeedbackCreateResponse
from vecinita_shared_schemas.internal_write import (
    AuditCleanupResponse,
    AuditEventRequest,
    AuditEventResponse,
    AuditLogResponse,
    FeedbackListResponse,
)
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.validation import validate_feedback_request

from vecinita_internal_write_api.audit import cleanup_audit_log, emit_audit_event
from vecinita_internal_write_api.audit_service import fetch_audit_log
from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.feedback import cleanup_feedback, insert_feedback, list_feedback
from vecinita_internal_write_api.feedback_notify import (
    FeedbackNotifyPayload,
    notify_feedback_operators,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_audit_feedback_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register audit log, audit ingest, cleanup, and feedback routes."""

    @app.get(
        "/internal/v1/audit",
        response_model=AuditLogResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_audit_log_route(  # noqa: PLR0913  # pyright: ignore[reportUnusedFunction]
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        actor_id: UUID | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> AuditLogResponse:
        return fetch_audit_log(
            engine=engine,
            page=page,
            page_size=page_size,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            since=since,
            until=until,
        )

    @app.post(
        "/internal/v1/audit/event",
        response_model=AuditEventResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=[Depends(require_service)],
    )
    def ingest_audit_event_route(body: AuditEventRequest) -> AuditEventResponse:  # pyright: ignore[reportUnusedFunction]
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            emit_audit_event(
                conn,
                event_type=body.event_type,
                entity_type=body.entity_type,
                entity_id=body.entity_id,
                request_id=request_id,
                payload=body.payload,
                actor_id=body.actor_id,
                actor_role=body.actor_role,
            )
        return AuditEventResponse()

    @app.post(
        "/internal/v1/audit/cleanup",
        response_model=AuditCleanupResponse,
    )
    def audit_cleanup_route(_actor: WriteActorDep) -> AuditCleanupResponse:  # pyright: ignore[reportUnusedFunction]
        retention_days = int(os.environ.get("VECINITA_AUDIT_RETENTION_DAYS", "365"))
        if retention_days <= 0:
            return AuditCleanupResponse(deleted=0, retention_days=retention_days)
        deleted = cleanup_audit_log(engine, retention_days=retention_days)
        return AuditCleanupResponse(deleted=deleted, retention_days=retention_days)

    @app.post(
        "/internal/v1/feedback/cleanup",
        response_model=AuditCleanupResponse,
    )
    def feedback_cleanup_route(_actor: WriteActorDep) -> AuditCleanupResponse:  # pyright: ignore[reportUnusedFunction]
        retention_days = int(os.environ.get("VECINITA_FEEDBACK_RETENTION_DAYS", "90"))
        if retention_days <= 0:
            return AuditCleanupResponse(deleted=0, retention_days=retention_days)
        deleted = cleanup_feedback(engine, retention_days=retention_days)
        return AuditCleanupResponse(deleted=deleted, retention_days=retention_days)

    @app.post(
        "/internal/v1/feedback",
        response_model=FeedbackCreateResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_feedback_route(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        _actor: WriteActorDep,
    ) -> FeedbackCreateResponse:
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
        with engine.begin() as conn:
            created = insert_feedback(conn, body)
        notify_feedback_operators(
            FeedbackNotifyPayload(
                id=str(created.id),
                category=body.category,
                locale=body.locale,
                created_at=created.created_at,
                message=body.message,
            )
        )
        return created

    @app.get(
        "/internal/v1/feedback",
        response_model=FeedbackListResponse,
    )
    def get_feedback_list_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        category: Annotated[str | None, Query()] = None,
    ) -> FeedbackListResponse:
        return list_feedback(
            engine,
            page=page,
            page_size=page_size,
            category=category,
        )

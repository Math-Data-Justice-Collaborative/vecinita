"""Single-document retag enqueue with audit."""

from __future__ import annotations

import uuid as _uuid
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.internal_write import RetagJobResponse

from vecinita_internal_write_api.audit import emit_audit_event
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def enqueue_document_retag(  # noqa: PLR0913  # actor + auth surface
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
    document_id: UUID,
    actor_id: UUID | None,
    actor_role: str | None,
    authorization: str | None,
) -> RetagJobResponse:
    """Enqueue a retag job for one document."""
    if retag_jobs is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retag job client not configured",
        )
    request_id = _uuid.uuid4()
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT id FROM documents WHERE id = :document_id"),
            {"document_id": document_id},
        ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        try:
            job_id = retag_jobs.enqueue_retag(
                document_id,
                authorization=authorization,
            )
        except DataManagementJobsClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        emit_audit_event(
            conn,
            event_type="document.retagged",
            entity_type="document",
            entity_id=document_id,
            request_id=request_id,
            payload={"job_id": str(job_id)},
            actor_id=actor_id,
            actor_role=actor_role,
        )
    return RetagJobResponse(job_id=job_id)

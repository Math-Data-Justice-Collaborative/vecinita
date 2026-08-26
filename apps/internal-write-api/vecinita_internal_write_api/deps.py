"""Shared FastAPI dependencies and row-mapping helpers for internal write API."""

from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING, Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import create_engine
from vecinita_shared_schemas.audit_headers import (
    AUDIT_ACTOR_ID_HEADER,
    AUDIT_ACTOR_ROLE_HEADER,
)
from vecinita_shared_schemas.auth import (
    AuthContext,
    AuthPrincipal,
    is_admin_role,
    require_admin_write,
    require_authenticated,
    require_super_admin,
)
from vecinita_shared_schemas.db_mapping import (
    row_datetime,  # noqa: F401  # re-export for internal-write-api services
    row_datetime_optional,  # noqa: F401  # re-export for internal-write-api services
    row_str,
)
from vecinita_shared_schemas.internal_write import TagInput
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.engine import Engine

MAX_DOCUMENT_TAGS = 10


def dependency_health_url(base: str) -> str:
    """Build liveness URL for an upstream base that may already end with /health."""
    normalized = base.rstrip("/")
    if normalized.endswith("/health"):
        return normalized
    return f"{normalized}/health"


def document_url_key(url: object) -> str:
    """Normalize document URLs for lookup (Pydantic HttpUrl adds a trailing slash)."""
    return str(url).rstrip("/")


def tags_snapshot_list(value: object) -> list[dict[str, object]]:
    """Normalize a JSON tags snapshot list for document version rows."""
    if not isinstance(value, list):
        return []
    value_list: list[object] = cast("list[object]", value)
    return [
        as_json_object(cast("object", raw_item))
        for raw_item in value_list
        if isinstance(raw_item, dict)
    ]


def tag_input_from_row(tag: Mapping[str, object]) -> TagInput:
    """Build a TagInput from a joined tag row."""
    return TagInput.model_validate(
        {
            "slug": row_str(tag, "slug"),
            "label": row_str(tag, "label"),
            "source": row_str(tag, "source"),
        }
    )


def normalize_database_url(url: str) -> str:
    """Upgrade plain postgresql:// URLs to psycopg driver form."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def database_url() -> str:
    """Resolve DATABASE_URL for the internal write API."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is required for internal write API"
        raise RuntimeError(msg)
    return normalize_database_url(url)


def engine() -> Engine:
    """Create the SQLAlchemy engine for corpus writes."""
    return create_engine(database_url())


def resolve_write_actor(
    ctx: Annotated[AuthContext, Depends(require_admin_write)],
    request: Request,
) -> tuple[UUID | None, str | None]:
    """Resolved operator actor for audit attribution on write routes."""
    if ctx.is_service:
        actor_hdr = request.headers.get(AUDIT_ACTOR_ID_HEADER)
        if actor_hdr:
            with contextlib.suppress(ValueError):
                return (UUID(actor_hdr), request.headers.get(AUDIT_ACTOR_ROLE_HEADER))
        return (None, None)
    if ctx.principal is None:
        return (None, None)
    return (ctx.principal.sub, ctx.principal.role)


def resolve_read_actor(
    ctx: Annotated[AuthContext, Depends(require_authenticated)],
) -> tuple[UUID | None, str | None]:
    """Resolved operator actor for authenticated read routes (admin or viewer)."""
    if ctx.is_service or ctx.principal is None:
        return (None, None)
    return (ctx.principal.sub, ctx.principal.role)


def resolve_admin_read_actor(
    ctx: Annotated[AuthContext, Depends(require_authenticated)],
) -> AuthPrincipal:
    """Admin or super-admin operator JWT for production config read routes."""
    if ctx.is_service or ctx.principal is None or not is_admin_role(ctx.principal.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx.principal


def resolve_super_admin_actor(
    ctx: Annotated[AuthContext, Depends(require_super_admin)],
) -> UUID:
    """Super-admin operator id for promote routes."""
    if ctx.principal is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx.principal.sub


AdminReadActorDep = Annotated[AuthPrincipal, Depends(resolve_admin_read_actor)]
SuperAdminActorDep = Annotated[UUID, Depends(resolve_super_admin_actor)]
WriteActorDep = Annotated[tuple[UUID | None, str | None], Depends(resolve_write_actor)]
ReadActorDep = Annotated[tuple[UUID | None, str | None], Depends(resolve_read_actor)]

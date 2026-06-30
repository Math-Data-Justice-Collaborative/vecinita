"""`/admin/users*` route registration for the DM backend (EV-006 F35, ADR-030 §1/§3).

Admin-only namespace that wraps the Supabase GoTrue Admin API server-side. Every mutation
emits a PII-free audit event via the internal write API. Lockout guards (self/last-admin) live
in ``UserAdminService``; this layer maps domain errors to HTTP and applies the invite rate limit.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003  # FastAPI path params require UUID at runtime

from fastapi import Depends, HTTPException, Query, status
from vecinita_shared_schemas.data_management import (
    AcknowledgedResponse,
    InviteUserRequest,
    RoleUpdateRequest,
    UserListResponse,
    UserSummary,
)
from vecinita_shared_schemas.internal_write import AuditEventRequest
from vecinita_shared_schemas.supabase_admin import SupabaseAdminError

from vecinita_data_management_backend.user_admin import LockoutError, UserAdminService

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI
    from vecinita_shared_schemas.auth import AuthPrincipal
    from vecinita_shared_schemas.supabase_admin import AdminUser, SupabaseAdminClient

    from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter

_logger = logging.getLogger(__name__)
_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 200


def _to_summary(user: AdminUser) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_sign_in_at=user.last_sign_in_at,
    )


def _map_admin_error(err: SupabaseAdminError) -> HTTPException:
    if err.status_code == HTTPStatus.NOT_FOUND:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if err.status_code in {HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_ENTITY}:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Upstream auth service error",
    )


def _lockout_http(err: LockoutError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": err.code, "message": str(err)},
    )


def register_user_admin_routes(  # noqa: C901, PLR0915  # FastAPI registers all admin routes inline
    app: FastAPI,
    *,
    admin_client: SupabaseAdminClient | None,
    audit_emit: Callable[[AuditEventRequest], None],
    invite_limiter: SlidingWindowRateLimiter,
    write_auth_dep: Callable[..., AuthPrincipal],
) -> None:
    """Mount the admin user-management routes; a missing client yields 503 per route."""
    service = UserAdminService(admin_client) if admin_client is not None else None

    def _require_client() -> SupabaseAdminClient:
        if admin_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User management is not configured",
            )
        return admin_client

    def _require_service() -> UserAdminService:
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User management is not configured",
            )
        return service

    def _audit(
        event_type: str,
        entity_id: UUID,
        actor: AuthPrincipal,
        payload: dict[str, object] | None = None,
    ) -> None:
        try:
            audit_emit(
                AuditEventRequest(
                    event_type=event_type,
                    entity_type="user",
                    entity_id=entity_id,
                    payload=payload or {},
                    actor_id=actor.sub,
                    actor_role=actor.role,
                )
            )
        except Exception:  # noqa: BLE001  # audit is best-effort; never fail the mutation
            _logger.warning("audit emit failed for %s", event_type, exc_info=True)

    @app.get("/admin/users", response_model=UserListResponse)
    def list_users(  # pyright: ignore[reportUnusedFunction]
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
        _auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> UserListResponse:
        svc = _require_service()
        try:
            result = svc.list_users(page=page, per_page=page_size)
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        return UserListResponse(
            users=[_to_summary(user) for user in result.users],
            total=result.total,
            page=page,
            page_size=page_size,
        )

    @app.post(
        "/admin/users/invite",
        status_code=status.HTTP_201_CREATED,
        response_model=UserSummary,
    )
    def invite_user(  # pyright: ignore[reportUnusedFunction]
        body: InviteUserRequest,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> UserSummary:
        client = _require_client()
        if not invite_limiter.allow(str(actor.sub)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Invite rate limit exceeded; try again later",
            )
        try:
            invited = client.invite_user_by_email(body.email)
            user = client.update_user_by_id(invited.id, role=body.role)
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.invited", user.id, actor, {"role": body.role})
        return _to_summary(user)

    @app.patch("/admin/users/{user_id}/role", response_model=UserSummary)
    def change_role(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        body: RoleUpdateRequest,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> UserSummary:
        svc = _require_service()
        try:
            user = svc.change_role(actor_id=actor.sub, target_id=user_id, new_role=body.role)
        except LockoutError as err:
            raise _lockout_http(err) from err
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.role_changed", user_id, actor, {"role": body.role})
        return _to_summary(user)

    @app.post(
        "/admin/users/{user_id}/resend-invite",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=AcknowledgedResponse,
    )
    def resend_invite(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> AcknowledgedResponse:
        client = _require_client()
        try:
            target = client.get_user_by_id(user_id)
            client.invite_user_by_email(target.email)
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.invited", user_id, actor, {"resend": True})
        return AcknowledgedResponse()

    @app.post("/admin/users/{user_id}/disable", response_model=UserSummary)
    def disable_user(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> UserSummary:
        svc = _require_service()
        try:
            user = svc.disable_user(actor_id=actor.sub, target_id=user_id)
        except LockoutError as err:
            raise _lockout_http(err) from err
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.disabled", user_id, actor)
        return _to_summary(user)

    @app.post("/admin/users/{user_id}/enable", response_model=UserSummary)
    def enable_user(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> UserSummary:
        svc = _require_service()
        try:
            user = svc.enable_user(target_id=user_id)
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.enabled", user_id, actor)
        return _to_summary(user)

    @app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_user(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> None:
        svc = _require_service()
        try:
            svc.delete_user(actor_id=actor.sub, target_id=user_id)
        except LockoutError as err:
            raise _lockout_http(err) from err
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.deleted", user_id, actor)

    @app.post(
        "/admin/users/{user_id}/reset-password",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=AcknowledgedResponse,
    )
    def reset_password(  # pyright: ignore[reportUnusedFunction]
        user_id: UUID,
        actor: AuthPrincipal = Depends(write_auth_dep),
    ) -> AcknowledgedResponse:
        client = _require_client()
        try:
            target = client.get_user_by_id(user_id)
            client.send_password_recovery(target.email)
        except SupabaseAdminError as err:
            raise _map_admin_error(err) from err
        _audit("user.reset_password", user_id, actor)
        return AcknowledgedResponse()

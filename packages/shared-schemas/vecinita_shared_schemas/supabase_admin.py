"""Supabase GoTrue Admin REST client (EV-006 F35, ADR-030 §2, TP-S005-02).

A thin, strictly-typed ``httpx`` wrapper over the Supabase Auth Admin API
(``{SUPABASE_URL}/auth/v1/admin/*`` and ``/auth/v1/invite``). We intentionally do **not**
depend on ``supabase-py`` (it pulls postgrest/storage/realtime and complicates strict typing
under ADR-018). The ``SUPABASE_SECRET_KEY`` is server-side only and never reaches the browser.
"""

from __future__ import annotations

import os
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal, Protocol, cast
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Mapping

import httpx
from pydantic import BaseModel

from vecinita_shared_schemas.auth import Role
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_ENV_URL: Final[str] = "SUPABASE_URL"
_ENV_SECRET: Final[str] = "SUPABASE_SECRET_KEY"  # noqa: S105  # env var name, not a secret

UserStatus = Literal["active", "invited", "disabled"]
LinkType = Literal["recovery", "invite", "magiclink"]


class _JsonBody(Protocol):
    def json(self) -> object: ...


def _json_object(response: _JsonBody) -> JsonObject:
    """Parse an httpx response body as a JSON object (reportAny-safe)."""
    return as_json_object(response.json())


class SupabaseAdminError(RuntimeError):
    """Raised when Admin API configuration or a request fails."""

    def __init__(self, message: str, *, status_code: int = 0) -> None:
        """Capture the failing HTTP status code (0 for configuration errors)."""
        super().__init__(message)
        self.status_code = status_code


class AdminUser(BaseModel):
    """Operator identity projected from a GoTrue user object (no PII beyond email)."""

    id: UUID
    email: str
    role: Role | None = None
    status: UserStatus
    created_at: datetime | None = None
    last_sign_in_at: datetime | None = None

    @classmethod
    def from_gotrue(cls, payload: JsonObject) -> AdminUser:
        """Build an AdminUser from a raw GoTrue user object."""
        return cls(
            id=UUID(_str(payload, "id")),
            email=_str(payload, "email"),
            role=_role(payload),
            status=_status(payload),
            created_at=_dt_optional(payload, "created_at"),
            last_sign_in_at=_dt_optional(payload, "last_sign_in_at"),
        )


class ListUsersResult(BaseModel):
    """Paged result of a GoTrue admin user list."""

    users: list[AdminUser]
    total: int | None = None


def _str(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        msg = f"Expected string for GoTrue field {key!r}"
        raise SupabaseAdminError(msg)
    return value


def _dt_optional(payload: JsonObject, key: str) -> datetime | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _role(payload: JsonObject) -> Role | None:
    app_meta = payload.get("app_metadata")
    if not isinstance(app_meta, dict):
        return None
    role_raw = cast("dict[str, object]", app_meta).get("role")
    if role_raw == "admin":
        return "admin"
    if role_raw == "viewer":
        return "viewer"
    return None


def _status(payload: JsonObject) -> UserStatus:
    if payload.get("banned_until"):
        return "disabled"
    if payload.get("email_confirmed_at") or payload.get("last_sign_in_at"):
        return "active"
    return "invited"


class SupabaseAdminClient:
    """Call the Supabase GoTrue Admin REST API with the service (secret) key."""

    def __init__(
        self,
        base_url: str | None = None,
        secret_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Resolve the Supabase URL + secret key from arguments or environment."""
        resolved_url = (base_url or os.environ.get(_ENV_URL) or "").rstrip("/")
        resolved_key = secret_key or os.environ.get(_ENV_SECRET)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_URL} and {_ENV_SECRET} are required"
            raise SupabaseAdminError(msg)
        self._base_url = resolved_url
        self._secret = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=resolved_url, timeout=timeout)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        return {"apikey": self._secret, "Authorization": f"Bearer {self._secret}"}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: JsonObject | None = None,
    ) -> httpx.Response:
        response = self._client.request(
            method,
            path,
            params=params,
            json=body,
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"{method} {path} failed: {response.status_code} {response.text}"
            raise SupabaseAdminError(msg, status_code=response.status_code)
        return response

    def list_users(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        user_filter: str | None = None,
    ) -> ListUsersResult:
        """List operators (GoTrue admin users), optionally filtered by email substring."""
        params = {"page": str(page), "per_page": str(per_page)}
        if user_filter:
            params["filter"] = user_filter
        response = self._request("GET", "/auth/v1/admin/users", params=params)
        payload = _json_object(response)
        raw_users = payload.get("users")
        users: list[AdminUser] = []
        if isinstance(raw_users, list):
            raw_list = cast("list[object]", raw_users)
            users = [AdminUser.from_gotrue(as_json_object(item)) for item in raw_list]
        headers = cast("Mapping[str, str]", response.headers)
        total_header = headers.get("x-total-count")
        total = int(total_header) if total_header is not None and total_header.isdigit() else None
        return ListUsersResult(users=users, total=total)

    def get_user_by_id(self, user_id: UUID) -> AdminUser:
        """Fetch a single operator by id."""
        response = self._request("GET", f"/auth/v1/admin/users/{user_id}")
        return AdminUser.from_gotrue(_json_object(response))

    def invite_user_by_email(self, email: str, *, redirect_to: str | None = None) -> AdminUser:
        """Invite a new operator by email (sends the repo-versioned invite template)."""
        params = {"redirect_to": redirect_to} if redirect_to else None
        response = self._request("POST", "/auth/v1/invite", params=params, body={"email": email})
        return AdminUser.from_gotrue(_json_object(response))

    def update_user_by_id(
        self,
        user_id: UUID,
        *,
        role: Role | None = None,
        ban_duration: str | None = None,
    ) -> AdminUser:
        """Update an operator's role (app_metadata) and/or ban state."""
        body: JsonObject = {}
        if role is not None:
            body["app_metadata"] = {"role": role}
        if ban_duration is not None:
            body["ban_duration"] = ban_duration
        response = self._request("PUT", f"/auth/v1/admin/users/{user_id}", body=body)
        return AdminUser.from_gotrue(_json_object(response))

    def delete_user(self, user_id: UUID) -> None:
        """Permanently delete an operator."""
        self._request("DELETE", f"/auth/v1/admin/users/{user_id}")

    def send_password_recovery(self, email: str, *, redirect_to: str | None = None) -> None:
        """Trigger a recovery email (sends via the configured SMTP + recovery template)."""
        params = {"redirect_to": redirect_to} if redirect_to else None
        self._request("POST", "/auth/v1/recover", params=params, body={"email": email})

    def generate_link(
        self,
        link_type: LinkType,
        email: str,
        *,
        redirect_to: str | None = None,
    ) -> str:
        """Generate an action link (e.g. recovery) and return its URL."""
        body: JsonObject = {"type": link_type, "email": email}
        if redirect_to:
            body["redirect_to"] = redirect_to
        response = self._request("POST", "/auth/v1/admin/generate_link", body=body)
        payload = _json_object(response)
        action_link = payload.get("action_link")
        return action_link if isinstance(action_link, str) else ""

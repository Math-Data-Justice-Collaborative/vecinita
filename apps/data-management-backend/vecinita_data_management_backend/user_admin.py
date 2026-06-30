"""Operator user-management service with lockout guards (EV-006 F35, ADR-030 §4).

Modal-agnostic core logic. Wraps the Supabase GoTrue Admin client and enforces that an admin
cannot delete/disable/demote their own account or the sole remaining active admin (TP-S005-04).
Mutations that pass the guards delegate to the Admin client; the route layer (M50) handles
auth, audit emission, and HTTP mapping (LockoutError -> 409).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_shared_schemas.auth import Role
    from vecinita_shared_schemas.supabase_admin import (
        AdminUser,
        ListUsersResult,
        SupabaseAdminClient,
    )

# GoTrue ban duration used to disable an account (~100 years).
BAN_FOREVER: Final[str] = "876000h"
BAN_NONE: Final[str] = "none"

# Machine-readable lockout codes (route layer maps both to HTTP 409).
LOCKOUT_SELF_ACTION: Final[str] = "self_action"
LOCKOUT_LAST_ADMIN: Final[str] = "last_admin"


class LockoutError(RuntimeError):
    """Raised when a user-management action would lock the operator team out of admin access."""

    def __init__(self, code: str, message: str) -> None:
        """Capture a machine-readable code (`self_action` | `last_admin`)."""
        super().__init__(message)
        self.code = code


class UserAdminService:
    """Apply lockout guards around Supabase Admin user mutations."""

    def __init__(self, client: SupabaseAdminClient) -> None:
        """Wrap a configured Supabase Admin client."""
        self._client = client

    def list_users(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        user_filter: str | None = None,
    ) -> ListUsersResult:
        """List operators (pass-through to the Admin client)."""
        return self._client.list_users(page=page, per_page=per_page, user_filter=user_filter)

    def count_active_admins(self) -> int:
        """Count operators with role admin that are not disabled."""
        per_page = 200
        page = 1
        total = 0
        while True:
            result = self._client.list_users(page=page, per_page=per_page)
            total += sum(
                1 for u in result.users if u.role == "admin" and u.status != "disabled"
            )
            if len(result.users) < per_page:
                break
            page += 1
        return total

    def _ensure_not_self(self, actor_id: UUID | None, target_id: UUID, action: str) -> None:
        if actor_id is not None and actor_id == target_id:
            msg = f"You cannot {action} your own account."
            raise LockoutError(LOCKOUT_SELF_ACTION, msg)

    def _ensure_not_last_admin(self, target: AdminUser, action: str) -> None:
        if (
            target.role == "admin"
            and target.status != "disabled"
            and self.count_active_admins() <= 1
        ):
            msg = f"Cannot {action} the last remaining admin."
            raise LockoutError(LOCKOUT_LAST_ADMIN, msg)

    def delete_user(self, *, actor_id: UUID | None, target_id: UUID) -> None:
        """Delete an operator after self/last-admin guards."""
        target = self._client.get_user_by_id(target_id)
        self._ensure_not_self(actor_id, target_id, "delete")
        self._ensure_not_last_admin(target, "delete")
        self._client.delete_user(target_id)

    def disable_user(self, *, actor_id: UUID | None, target_id: UUID) -> AdminUser:
        """Ban (disable) an operator after self/last-admin guards."""
        target = self._client.get_user_by_id(target_id)
        self._ensure_not_self(actor_id, target_id, "disable")
        self._ensure_not_last_admin(target, "disable")
        return self._client.update_user_by_id(target_id, ban_duration=BAN_FOREVER)

    def enable_user(self, *, target_id: UUID) -> AdminUser:
        """Un-ban (enable) an operator. No guard required."""
        return self._client.update_user_by_id(target_id, ban_duration=BAN_NONE)

    def change_role(self, *, actor_id: UUID | None, target_id: UUID, new_role: Role) -> AdminUser:
        """Change an operator's role; demoting the last/own admin is blocked."""
        target = self._client.get_user_by_id(target_id)
        if target.role == "admin" and new_role == "viewer":
            self._ensure_not_self(actor_id, target_id, "demote")
            self._ensure_not_last_admin(target, "demote")
        return self._client.update_user_by_id(target_id, role=new_role)

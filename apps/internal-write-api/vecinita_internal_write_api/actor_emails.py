"""Read-time actor_email resolution from Supabase Auth (F69 / EV-024).

Emails are never stored on ``audit_log`` — only looked up when listing audit
rows (api-contract.md GET /internal/v1/audit; S026-D19).
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Final

from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient, SupabaseAdminError

if TYPE_CHECKING:
    from uuid import UUID

_LOG = logging.getLogger(__name__)

# Short TTL: enough to dedupe a page of audit rows / repeat filters in a session.
_CACHE_TTL_SECONDS: Final[float] = 300.0

# Sentinel email for negative cache (Admin miss); never returned to callers.
_MISS: Final[str] = ""


class ActorEmailResolver:
    """Resolve actor UUIDs → emails via Supabase Admin with an in-process TTL cache."""

    def __init__(
        self,
        client: SupabaseAdminClient | None = None,
        *,
        ttl_seconds: float = _CACHE_TTL_SECONDS,
    ) -> None:
        """Optionally inject an Admin client (tests); else built from env on demand."""
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[UUID, tuple[float, str]] = {}

    def clear_cache(self) -> None:
        """Drop all cached hits and misses (tests)."""
        self._cache.clear()

    def _get_client(self) -> SupabaseAdminClient | None:
        if self._client is not None:
            return self._client
        try:
            return SupabaseAdminClient()
        except SupabaseAdminError:
            _LOG.debug("Supabase Admin unavailable; actor_email enrich skipped")
            return None

    def resolve(self, user_ids: list[UUID]) -> dict[UUID, str]:
        """Return ``{actor_id: email}`` for resolvable ids; omit misses."""
        unique = list(dict.fromkeys(user_ids))
        if not unique:
            return {}

        now = time.monotonic()
        out: dict[UUID, str] = {}
        missing: list[UUID] = []

        for uid in unique:
            cached = self._cache.get(uid)
            if cached is not None:
                cached_at, email = cached
                if now - cached_at < self._ttl:
                    if email != _MISS:
                        out[uid] = email
                    continue
            missing.append(uid)

        if not missing:
            return out

        client = self._get_client()
        if client is None:
            return out

        for uid in missing:
            email = self._lookup_one(client, uid)
            self._cache[uid] = (now, email if email is not None else _MISS)
            if email is not None:
                out[uid] = email
        return out

    @staticmethod
    def _lookup_one(client: SupabaseAdminClient, user_id: UUID) -> str | None:
        try:
            user = client.get_user_by_id(user_id)
        except SupabaseAdminError:
            return None
        if user.email:
            return user.email
        return None


_default_resolver = ActorEmailResolver()


def resolve_actor_emails(
    user_ids: list[UUID],
    *,
    client: SupabaseAdminClient | None = None,
) -> dict[UUID, str]:
    """Module-level entry used by GET /internal/v1/audit (monkeypatch target in e2e)."""
    if client is not None:
        return ActorEmailResolver(client=client).resolve(user_ids)
    return _default_resolver.resolve(user_ids)


def reset_actor_email_cache_for_tests() -> None:
    """Clear the process-wide resolver cache between tests."""
    _default_resolver.clear_cache()

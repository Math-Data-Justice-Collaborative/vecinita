"""F76 corpus freshness policy helpers (stale threshold, hash skip, enqueue).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_FRESHNESS_*]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/decisions.md §RD-337]
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

FRESHNESS_ENABLED_ENV = "VECINITA_FRESHNESS_ENABLED"
FRESHNESS_STALE_DAYS_ENV = "VECINITA_FRESHNESS_STALE_DAYS"

DEFAULT_FRESHNESS_ENABLED = False
DEFAULT_FRESHNESS_STALE_DAYS = 30

FreshnessEnqueueDecision = Literal[
    "enqueue",
    "skip_disabled",
    "skip_kill_switch",
    "skip_refresh_disabled",
    "skip_not_stale",
]

HashRefreshDecision = Literal["rechunk", "skip_rechunk"]

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off", ""})


@dataclass(frozen=True, slots=True)
class FreshnessEnqueueRequest:
    """Inputs for a single freshness_refresh enqueue decision (F76)."""

    freshness_enabled: bool
    kill_switch: bool
    refresh_enabled: bool
    is_stale: bool
    force: bool
    document_id: UUID


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return default


def is_freshness_enabled() -> bool:
    """Return whether F76 schedule refresh master enable is on (default false)."""
    return _env_bool(FRESHNESS_ENABLED_ENV, default=DEFAULT_FRESHNESS_ENABLED)


def parse_freshness_stale_days() -> int:
    """Parse stale threshold days (default 30 — RD-337 / AC-FR1)."""
    raw = os.environ.get(FRESHNESS_STALE_DAYS_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_FRESHNESS_STALE_DAYS
    try:
        value = int(raw.strip(), 10)
    except ValueError:
        return DEFAULT_FRESHNESS_STALE_DAYS
    if value < 1:
        return DEFAULT_FRESHNESS_STALE_DAYS
    return value


def is_document_stale(
    last_checked_at: datetime | None,
    *,
    now: datetime,
    stale_days: int,
) -> bool:
    """True when never checked or last_checked is older than the stale threshold."""
    if last_checked_at is None:
        return True
    return last_checked_at <= now - timedelta(days=stale_days)


def decide_freshness_enqueue(request: FreshnessEnqueueRequest) -> FreshnessEnqueueDecision:
    """Decide whether to enqueue ``freshness_refresh`` for one URL source.

    Kill-switch and per-source ``refresh_enabled`` always apply. Scheduled ticks
    require master enable + stale; ``force`` (Refresh now) bypasses the stale check
    only (TC-256-259 / AC-FR1-FR4).
    """
    if request.kill_switch:
        return "skip_kill_switch"
    if not request.freshness_enabled:
        return "skip_disabled"
    if not request.refresh_enabled:
        return "skip_refresh_disabled"
    if not request.force and not request.is_stale:
        return "skip_not_stale"
    return "enqueue"


def decide_hash_aware_refresh(
    *,
    stored_hash: str | None,
    fetched_hash: str,
) -> HashRefreshDecision:
    """Hash-aware refresh: unchanged content skips rechunk (AC-FR2 / TC-257)."""
    if stored_hash is not None and stored_hash == fetched_hash:
        return "skip_rechunk"
    return "rechunk"


def should_bump_last_checked_after_refresh(_decision: HashRefreshDecision) -> bool:
    """Always bump ``last_checked_at`` after a completed refresh check (RD-337)."""
    return True


def freshness_enqueues_catchup() -> bool:
    """AC-FR5: freshness must not fire F75 catch-up side effects."""
    return False

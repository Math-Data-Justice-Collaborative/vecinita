"""F75 corpus automation catch-up policy helpers (env + enqueue decisions).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_AUTOMATIONS_*]
[Spec: docs/acceptance-criteria.md §AC-AU1-AU3]
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

AUTOMATIONS_ENABLED_ENV = "VECINITA_AUTOMATIONS_ENABLED"
AUTOMATIONS_KILL_SWITCH_ENV = "VECINITA_AUTOMATIONS_KILL_SWITCH"
AUTOMATIONS_MAX_CONCURRENT_ENV = "VECINITA_AUTOMATIONS_MAX_CONCURRENT"

DEFAULT_AUTOMATIONS_ENABLED = False
DEFAULT_AUTOMATIONS_KILL_SWITCH = False
DEFAULT_AUTOMATIONS_MAX_CONCURRENT = 2

EmbedStatus = Literal["complete", "missing", "partial", "failed"]
CatchupEnqueueDecision = Literal[
    "enqueue",
    "skip_disabled",
    "skip_kill_switch",
    "skip_complete",
    "skip_duplicate",
    "skip_at_capacity",
]

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off", ""})


@dataclass(frozen=True, slots=True)
class CatchupEnqueueRequest:
    """Inputs for a single catch-up enqueue decision (F75)."""

    enabled: bool
    kill_switch: bool
    embed_status: EmbedStatus
    idempotency_key: str
    seen_keys: frozenset[str]
    running_count: int
    max_concurrent: int


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


def is_automations_enabled() -> bool:
    """Return whether F75 master enable is on (default false)."""
    return _env_bool(AUTOMATIONS_ENABLED_ENV, default=DEFAULT_AUTOMATIONS_ENABLED)


def is_automations_kill_switch_on() -> bool:
    """Return whether the hard kill-switch blocks enqueue (default false)."""
    return _env_bool(
        AUTOMATIONS_KILL_SWITCH_ENV,
        default=DEFAULT_AUTOMATIONS_KILL_SWITCH,
    )


def parse_automations_max_concurrent() -> int:
    """Parse F75 concurrency cap (default 2)."""
    raw = os.environ.get(AUTOMATIONS_MAX_CONCURRENT_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    try:
        value = int(raw.strip(), 10)
    except ValueError:
        return DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    if value < 1:
        return DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    return value


def catchup_idempotency_key(*, document_id: UUID | str, revision: int | str) -> str:
    """Stable idempotent key ``document_id:revision`` (RD-335 / EV027-M1)."""
    return f"{document_id}:{revision}"


def decide_catchup_enqueue(request: CatchupEnqueueRequest) -> CatchupEnqueueDecision:
    """Decide whether to enqueue ``automation_catchup`` for one document revision.

    Catch-up only (RD-334): enqueue for missing/partial/failed embeds; never when
    embeddings are already complete. Kill-switch and enable flags take precedence
    over residual work (AC-AU1-AU2 / TC-252-254).
    """
    if request.kill_switch:
        return "skip_kill_switch"
    if not request.enabled:
        return "skip_disabled"
    if request.embed_status == "complete":
        return "skip_complete"
    if request.idempotency_key in request.seen_keys:
        return "skip_duplicate"
    if request.running_count >= request.max_concurrent:
        return "skip_at_capacity"
    return "enqueue"

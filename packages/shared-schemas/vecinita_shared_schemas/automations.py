"""F75 corpus automation catch-up policy helpers (env + enqueue decisions).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_AUTOMATIONS_*]
[Spec: docs/acceptance-criteria.md §AC-AU1-AU3]
[Spec: docs/api-contract.md §EV-027 Automations]
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


class CatchupJobsClient(Protocol):
    """Minimal Modal jobs client surface for catch-up enqueue (RD-335)."""

    def enqueue_automation_catchup(
        self,
        document_id: UUID,
        *,
        revision: str,
        embed_status: EmbedStatus,
        authorization: str | None = None,
    ) -> UUID:
        """Enqueue ``job_type=automation_catchup`` (async Modal worker)."""
        ...


def enqueue_catchup_targets(  # noqa: PLR0913  # gate inputs mirror CatchupEnqueueRequest
    jobs_client: CatchupJobsClient,
    *,
    targets: list[tuple[UUID, str, EmbedStatus]],
    enabled: bool,
    kill_switch: bool,
    running_count: int,
    max_concurrent: int,
    seen_keys: frozenset[str],
    authorization: str | None = None,
) -> list[tuple[CatchupEnqueueDecision, UUID | None]]:
    """Decide + optionally enqueue catch-up for each document revision (async only)."""
    results: list[tuple[CatchupEnqueueDecision, UUID | None]] = []
    seen = set(seen_keys)
    running = running_count
    for document_id, revision, embed_status in targets:
        key = catchup_idempotency_key(document_id=document_id, revision=revision)
        decision = decide_catchup_enqueue(
            CatchupEnqueueRequest(
                enabled=enabled,
                kill_switch=kill_switch,
                embed_status=embed_status,
                idempotency_key=key,
                seen_keys=frozenset(seen),
                running_count=running,
                max_concurrent=max_concurrent,
            )
        )
        if decision != "enqueue":
            results.append((decision, None))
            continue
        job_id = jobs_client.enqueue_automation_catchup(
            document_id,
            revision=revision,
            embed_status=embed_status,
            authorization=authorization,
        )
        seen.add(key)
        running += 1
        results.append((decision, job_id))
    return results


AutomationJobType = Literal["automation_catchup", "freshness_refresh"]
AutomationRunStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
    "blocked",
]


class AutomationsConfigResponse(BaseModel):
    """GET /internal/v1/automations/config (api-contract EV-027)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    kill_switch: bool
    max_concurrent: int = Field(..., ge=1)


class AutomationsConfigPatchRequest(BaseModel):
    """PATCH /internal/v1/automations/config — enable/disable (admin)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool


_CATCHUP_OUTCOME_TO_STATUS: dict[str, AutomationRunStatus] = {
    "reembedded": "completed",
    "skipped_complete": "skipped",
    "skipped_disabled": "skipped",
    "skipped_duplicate": "skipped",
    "skipped_at_capacity": "skipped",
    "skipped_kill_switch": "blocked",
    "failed": "failed",
}

_FRESHNESS_OUTCOME_TO_STATUS: dict[str, AutomationRunStatus] = {
    "refreshed": "completed",
    "verified_unchanged": "completed",
    "rechunked": "completed",
    "skipped_not_stale": "skipped",
    "skipped_disabled": "skipped",
    "skipped_refresh_disabled": "skipped",
    "skipped_kill_switch": "blocked",
    "failed": "failed",
}


def catchup_outcome_to_run_status(outcome: str) -> AutomationRunStatus:
    """Map catch-up worker outcome to ``automation_runs.status`` (TC-289)."""
    try:
        return _CATCHUP_OUTCOME_TO_STATUS[outcome]
    except KeyError:
        msg = f"unknown catch-up outcome: {outcome!r}"
        raise ValueError(msg) from None


def freshness_outcome_to_run_status(outcome: str) -> AutomationRunStatus:
    """Map freshness worker outcome to ``automation_runs.status`` (AC-FR7)."""
    try:
        return _FRESHNESS_OUTCOME_TO_STATUS[outcome]
    except KeyError:
        msg = f"unknown freshness outcome: {outcome!r}"
        raise ValueError(msg) from None


class AutomationRunCreateRequest(BaseModel):
    """POST /internal/v1/automations/runs — persist one history row (TC-289)."""

    model_config = ConfigDict(extra="forbid")

    job_type: AutomationJobType
    status: AutomationRunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    document_id: UUID | None = None
    revision: str | None = None


class AutomationRun(BaseModel):
    """One ``automation_runs`` row (TP3 / RD-341)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_type: AutomationJobType
    status: AutomationRunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    document_id: UUID | None = None
    revision: str | None = None
    created_at: datetime
    updated_at: datetime


class AutomationRunListResponse(BaseModel):
    """GET /internal/v1/automations/runs paginated history."""

    model_config = ConfigDict(extra="forbid")

    items: list[AutomationRun]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_count: int = Field(..., ge=0)


def load_automations_config_from_env() -> AutomationsConfigResponse:
    """Build config response from env (kill-switch + caps always env-backed)."""
    return AutomationsConfigResponse(
        enabled=is_automations_enabled(),
        kill_switch=is_automations_kill_switch_on(),
        max_concurrent=parse_automations_max_concurrent(),
    )

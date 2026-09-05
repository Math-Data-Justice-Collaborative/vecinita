"""Best-effort persist of automation_runs via write-API (TC-289 / ADR-052).

[Corpus: feature-list.md §F78]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/api-contract.md §EV-027 Automations]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_shared_schemas.automations import AutomationJobType, AutomationRunStatus

_logger = logging.getLogger(__name__)


def maybe_record_automation_run(  # noqa: PLR0913  # mirrors write-client record surface
    write_client: object,
    *,
    job_type: AutomationJobType,
    status: AutomationRunStatus,
    document_id: UUID | None = None,
    revision: str | None = None,
    error: str | None = None,
) -> None:
    """POST run history when the write client supports it; never raise to callers."""
    record = getattr(write_client, "record_automation_run", None)
    if not callable(record):
        return
    try:
        _ = record(
            job_type=job_type,
            status=status,
            document_id=document_id,
            revision=revision,
            error=error,
        )
    except Exception:  # noqa: BLE001  # history persist must not fail the parent job
        _logger.warning(
            "failed to persist automation_run job_type=%s document_id=%s",
            job_type,
            document_id,
            exc_info=True,
        )

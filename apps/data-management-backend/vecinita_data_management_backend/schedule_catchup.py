"""F75 daily catch-up schedule tick (ADR-052 / TC-289).

[Corpus: feature-list.md §F78]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-289]
"""

from __future__ import annotations

import logging

from vecinita_data_management_backend.automation_run_persist import (
    maybe_record_automation_run,
)

_logger = logging.getLogger(__name__)

TICK_RESULT = "automation_catchup_tick"


def record_scheduled_catchup_tick(write_client: object) -> str:
    """Persist a catch-up tick row (no residual scan; catch-up is job/CRUD driven)."""
    _logger.info("daily schedule tick: job_type=automation_catchup (shared Period(days=1))")
    maybe_record_automation_run(
        write_client,
        job_type="automation_catchup",
        status="completed",
        document_id=None,
        revision=None,
        error=None,
    )
    return TICK_RESULT

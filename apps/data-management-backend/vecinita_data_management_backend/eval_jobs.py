"""Map eval runs from internal-write-api into unified Job list rows (ADR-035 §3)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from vecinita_shared_schemas.data_management import Job

if TYPE_CHECKING:
    from vecinita_shared_schemas.internal_write import EvalRunListItem


def eval_run_to_job(item: EvalRunListItem) -> Job:
    """Convert an eval run list item to the shared Job schema."""
    created = item.started_at or item.completed_at or datetime.now(UTC)
    updated = item.completed_at or item.started_at or created
    return Job(
        job_id=item.run_id,
        status=item.status,
        job_type="eval",
        urls=[],
        error_code=None,
        error_message=item.error_message,
        created_at=created,
        updated_at=updated,
    )

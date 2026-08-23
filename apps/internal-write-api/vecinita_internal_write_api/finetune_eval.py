"""F77 finetune eval report store + lookup (T129.6 / TC-261).

In-process store for unit tests and early wiring. Adapter pin persistence for
promote/rollback lives in ``finetune_promote`` (T129.7).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-261]
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_shared_schemas.finetune_eval import FinetuneEvalReportResponse


class FinetuneEvalReportNotFoundError(LookupError):
    """No eval report registered for the finetune run id."""


class FinetuneEvalReportStore:
    """Thread-safe in-memory registry of base-vs-adapter FT eval reports."""

    def __init__(self) -> None:
        """Create an empty report map."""
        self._lock = Lock()
        self._reports: dict[UUID, FinetuneEvalReportResponse] = {}

    def put(self, report: FinetuneEvalReportResponse) -> None:
        """Upsert a report keyed by ``run_id``."""
        with self._lock:
            self._reports[report.run_id] = report

    def get(self, run_id: UUID) -> FinetuneEvalReportResponse:
        """Return the report or raise ``FinetuneEvalReportNotFoundError``."""
        with self._lock:
            report = self._reports.get(run_id)
        if report is None:
            msg = f"finetune eval report not found for run_id={run_id}"
            raise FinetuneEvalReportNotFoundError(msg)
        return report

    def clear(self) -> None:
        """Drop all reports (tests)."""
        with self._lock:
            self._reports.clear()


_STORE = FinetuneEvalReportStore()


def get_finetune_eval_store() -> FinetuneEvalReportStore:
    """Process-wide FT eval report store (injectable for tests via ``clear``/``put``)."""
    return _STORE

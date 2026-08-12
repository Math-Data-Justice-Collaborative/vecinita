"""Shared F75/F76 daily schedule dispatch planner (ADR-052 / TP2 / TC-264).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-264]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

DAILY_AUTOMATION_JOB_TYPES: Final[tuple[str, ...]] = (
    "automation_catchup",
    "freshness_refresh",
)


def plan_daily_dispatch() -> tuple[str, ...]:
    """Return ordered job types for the shared daily Modal schedule tick."""
    return DAILY_AUTOMATION_JOB_TYPES


def run_daily_dispatch(
    *,
    run_catchup: Callable[[], object],
    run_freshness: Callable[[], object],
) -> dict[str, object]:
    """Invoke catch-up then freshness branches for one schedule tick."""
    results: dict[str, object] = {}
    for job_type in plan_daily_dispatch():
        if job_type == "automation_catchup":
            results[job_type] = run_catchup()
        elif job_type == "freshness_refresh":
            results[job_type] = run_freshness()
    return results

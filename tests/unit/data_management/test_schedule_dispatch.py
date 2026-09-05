"""T127.7 — shared Modal daily schedule dispatches F75 then F76 job types (TC-264).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-264]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP2]
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from vecinita_data_management_backend.schedule_dispatch import (
    DAILY_AUTOMATION_JOB_TYPES,
    plan_daily_dispatch,
    run_daily_dispatch,
)

if TYPE_CHECKING:
    import pytest


def test_plan_daily_dispatch_orders_catchup_then_freshness() -> None:
    """TC-264 / TP2: one schedule; distinct job types; catch-up before freshness."""
    assert plan_daily_dispatch() == ("automation_catchup", "freshness_refresh")
    assert DAILY_AUTOMATION_JOB_TYPES == ("automation_catchup", "freshness_refresh")


def test_run_daily_dispatch_invokes_both_branches() -> None:
    """Shared tick runs both job-type branches (F76 freshness may no-op until M128)."""
    called: list[str] = []

    def run_catchup() -> str:
        called.append("automation_catchup")
        return "catchup_ok"

    def run_freshness() -> str:
        called.append("freshness_refresh")
        return "freshness_stub"

    results = run_daily_dispatch(run_catchup=run_catchup, run_freshness=run_freshness)
    assert called == ["automation_catchup", "freshness_refresh"]
    assert results == {
        "automation_catchup": "catchup_ok",
        "freshness_refresh": "freshness_stub",
    }


def test_run_daily_dispatch_skips_unknown_planned_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown planned job types are ignored (covers elif fall-through)."""
    monkeypatch.setattr(
        "vecinita_data_management_backend.schedule_dispatch.plan_daily_dispatch",
        lambda: ("automation_catchup", "unknown_type", "freshness_refresh"),
    )
    called: list[str] = []

    results = run_daily_dispatch(
        run_catchup=lambda: called.append("c") or "c",
        run_freshness=lambda: called.append("f") or "f",
    )
    assert called == ["c", "f"]
    assert "unknown_type" not in results
    assert results["automation_catchup"] == "c"
    assert results["freshness_refresh"] == "f"


def test_data_management_app_has_period_days_1_schedule() -> None:
    """ADR-052 / S030-D31 M2: schedule=modal.Period(days=1) on DM app."""
    path = Path(__file__).resolve().parents[3] / "infra" / "modal" / "data_management_app.py"
    source = path.read_text(encoding="utf-8")
    assert "schedule=modal.Period(days=1)" in source
    assert "daily_corpus_automations" in source
    assert "automation_catchup" in source
    assert "freshness_refresh" in source
    assert "record_scheduled_catchup_tick" in source

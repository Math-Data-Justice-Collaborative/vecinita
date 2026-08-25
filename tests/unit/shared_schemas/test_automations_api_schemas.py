"""T127.2 — Automations config + automation_runs schema shapes (api-contract EV-027).

[Corpus: feature-list.md §F75]
[Spec: docs/api-contract.md §EV-027 Automations]
[Spec: docs/test-plan.md §TC-255]
[Spec: docs/acceptance-criteria.md §AC-AU5]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.automations import (
    AutomationRun,
    AutomationRunCreateRequest,
    AutomationRunListResponse,
    AutomationsConfigPatchRequest,
    AutomationsConfigResponse,
    catchup_outcome_to_run_status,
    freshness_outcome_to_run_status,
    load_automations_config_from_env,
)

DOC_ID = UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")


def test_automations_config_response_shape() -> None:
    """GET config exposes enable, kill-switch, and concurrency cap."""
    cfg = AutomationsConfigResponse(
        enabled=True,
        kill_switch=False,
        max_concurrent=2,
    )
    assert cfg.model_dump() == {
        "enabled": True,
        "kill_switch": False,
        "max_concurrent": 2,
    }


def test_automations_config_patch_requires_enabled() -> None:
    """PATCH body is enable/disable only (admin)."""
    patch = AutomationsConfigPatchRequest(enabled=False)
    assert patch.enabled is False
    with pytest.raises(ValidationError):
        AutomationsConfigPatchRequest.model_validate({})


def test_automation_run_row_shape_matches_tp3() -> None:
    """automation_runs contract: status, job_type, timestamps, error, document key."""
    now = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    run_id = uuid4()
    run = AutomationRun(
        id=run_id,
        job_type="automation_catchup",
        status="completed",
        started_at=now,
        finished_at=now,
        error=None,
        document_id=DOC_ID,
        revision="3",
        created_at=now,
        updated_at=now,
    )
    dumped = run.model_dump()
    assert dumped["id"] == run_id
    assert dumped["job_type"] == "automation_catchup"
    assert dumped["status"] == "completed"
    assert dumped["document_id"] == DOC_ID
    assert dumped["revision"] == "3"
    assert dumped["error"] is None


def test_automation_run_list_response_pagination() -> None:
    """GET /automations/runs returns paginated items (TC-255 / AC-AU5)."""
    now = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    run = AutomationRun(
        id=uuid4(),
        job_type="freshness_refresh",
        status="failed",
        started_at=now,
        finished_at=now,
        error="fetch timeout",
        document_id=None,
        revision=None,
        created_at=now,
        updated_at=now,
    )
    listing = AutomationRunListResponse(
        items=[run],
        page=1,
        page_size=20,
        total_count=1,
    )
    assert listing.total_count == 1
    assert listing.items[0].job_type == "freshness_refresh"
    assert listing.items[0].error == "fetch timeout"


def test_automation_run_create_request_requires_job_type_and_status() -> None:
    """POST /automations/runs body is job_type + status; document key optional (TC-289)."""
    body = AutomationRunCreateRequest(
        job_type="automation_catchup",
        status="skipped",
        document_id=DOC_ID,
        revision="1",
        error=None,
    )
    dumped = body.model_dump()
    assert dumped["job_type"] == "automation_catchup"
    assert dumped["status"] == "skipped"
    assert dumped["document_id"] == DOC_ID
    assert dumped["revision"] == "1"
    assert dumped["started_at"] is None
    assert dumped["finished_at"] is None
    with pytest.raises(ValidationError):
        AutomationRunCreateRequest.model_validate({"job_type": "automation_catchup"})
    with pytest.raises(ValidationError):
        AutomationRunCreateRequest.model_validate(
            {"job_type": "automation_catchup", "status": "unknown"}
        )


def test_catchup_outcome_maps_to_automation_run_status() -> None:
    """Worker outcomes persist as automation_runs status (AC-AU5 / TC-289)."""
    assert catchup_outcome_to_run_status("reembedded") == "completed"
    assert catchup_outcome_to_run_status("skipped_complete") == "skipped"
    assert catchup_outcome_to_run_status("skipped_disabled") == "skipped"
    assert catchup_outcome_to_run_status("skipped_duplicate") == "skipped"
    assert catchup_outcome_to_run_status("skipped_at_capacity") == "skipped"
    assert catchup_outcome_to_run_status("skipped_kill_switch") == "blocked"
    assert catchup_outcome_to_run_status("failed") == "failed"


def test_freshness_outcome_maps_to_automation_run_status() -> None:
    """Freshness worker outcomes persist as automation_runs status (AC-FR7)."""
    assert freshness_outcome_to_run_status("refreshed") == "completed"
    assert freshness_outcome_to_run_status("verified_unchanged") == "completed"
    assert freshness_outcome_to_run_status("rechunked") == "completed"
    assert freshness_outcome_to_run_status("skipped_not_stale") == "skipped"
    assert freshness_outcome_to_run_status("skipped_disabled") == "skipped"
    assert freshness_outcome_to_run_status("skipped_refresh_disabled") == "skipped"
    assert freshness_outcome_to_run_status("skipped_kill_switch") == "blocked"
    assert freshness_outcome_to_run_status("failed") == "failed"


def test_load_automations_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env loader mirrors config-spec defaults and overrides."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_MAX_CONCURRENT", "4")
    cfg = load_automations_config_from_env()
    assert cfg == AutomationsConfigResponse(
        enabled=True,
        kill_switch=False,
        max_concurrent=4,
    )

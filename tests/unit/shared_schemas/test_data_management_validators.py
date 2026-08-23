"""Validator branch coverage for data_management admin request models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import (
    CreateJobRequest,
    EmailTestRequest,
    InviteUserRequest,
    JobOptions,
    UserSummary,
)


def test_invite_user_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        InviteUserRequest(email="not-an-email", role="viewer")


def test_email_test_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        EmailTestRequest(to="bad")


def test_email_test_request_accepts_valid_email() -> None:
    body = EmailTestRequest(to="ops@example.com")
    assert body.to == "ops@example.com"


def test_user_summary_accepts_super_admin_role() -> None:
    """UserSummary.role includes super-admin for auth-backed admin listings (ADR-035)."""
    summary = UserSummary(
        id=uuid4(),
        email="super@example.com",
        role="super-admin",
        status="active",
        created_at=datetime.now(UTC),
        last_sign_in_at=None,
    )
    assert summary.role == "super-admin"


def test_invite_user_request_rejects_super_admin_role() -> None:
    with pytest.raises(ValidationError):
        InviteUserRequest(email="ops@example.com", role="super-admin")  # type: ignore[arg-type]


def test_job_options_rejects_empty_translate_locales() -> None:
    """TC-252: translate_locales must be omitted or contain at least one locale."""
    with pytest.raises(ValidationError, match="translate_locales"):
        JobOptions.model_validate({"translate_locales": []})


def test_job_options_dedupes_translate_locales() -> None:
    """TC-252: duplicate translate_locales targets are collapsed."""
    options = JobOptions.model_validate({"translate_locales": ["es", "es"]})
    assert options.translate_locales == ["es"]


def test_create_job_request_requires_document_id_for_automation_catchup() -> None:
    """TC-266: automation_catchup jobs require document_id."""
    with pytest.raises(ValidationError, match="document_id"):
        CreateJobRequest.model_validate(
            {"urls": [], "options": {"job_type": "automation_catchup"}},
        )


def test_create_job_request_requires_document_id_for_freshness_refresh() -> None:
    """TC-270: freshness_refresh jobs require document_id."""
    with pytest.raises(ValidationError, match="document_id"):
        CreateJobRequest.model_validate(
            {"urls": [], "options": {"job_type": "freshness_refresh"}},
        )

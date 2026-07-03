"""Validator branch coverage for data_management admin request models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import (
    EmailTestRequest,
    InviteUserRequest,
    UserSummary,
)


def test_invite_user_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        InviteUserRequest(email="not-an-email", role="viewer")


def test_email_test_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        EmailTestRequest(to="bad")


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

"""Validator branch coverage for data_management admin request models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import EmailTestRequest, InviteUserRequest


def test_invite_user_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        InviteUserRequest(email="not-an-email", role="viewer")


def test_email_test_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        EmailTestRequest(to="bad")

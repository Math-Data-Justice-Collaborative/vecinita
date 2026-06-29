"""TC-030: reject identity fields in ChatRAG ask body (ADR-004)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.validation import (
    validate_ask_request,
)


def test_ask_request_rejects_email_field() -> None:
    """Test ask request rejects email field."""
    payload = {"question": "What are pantry hours?", "email": "a@b.com"}
    with pytest.raises(ValidationError) as exc_info:
        validate_ask_request(payload)
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("email",) for error in errors)


def test_ask_request_accepts_question_only() -> None:
    """Test ask request accepts question only."""
    result = validate_ask_request({"question": "What are pantry hours?"})
    assert result.question == "What are pantry hours?"

"""Public API validation — identity deny-list (ADR-004, config-spec)."""

from __future__ import annotations

from typing import Any, Final

from pydantic import ValidationError

from vecinita_shared_schemas.chat_rag import AskRequest

FORBIDDEN_IDENTITY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "email",
        "user_id",
        "name",
        "phone",
        "address",
        "session_id",
        "account_id",
        "profile",
        "invite",
    }
)


def find_identity_fields(payload: dict[str, Any]) -> list[str]:
    """Return identity field names present at the top level of a JSON body."""
    return sorted(key for key in payload if key in FORBIDDEN_IDENTITY_FIELDS)


def validate_ask_request(payload: dict[str, Any]) -> AskRequest:
    """Parse and validate ChatRAG ask body; reject identity fields explicitly."""
    identity = find_identity_fields(payload)
    if identity:
        field = identity[0]
        raise ValidationError.from_exception_data(
            "AskRequest",
            [
                {
                    "type": "extra_forbidden",
                    "loc": (field,),
                    "input": payload.get(field),
                }
            ],
        )
    return AskRequest.model_validate(payload)

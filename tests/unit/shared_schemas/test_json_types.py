"""Unit tests for vecinita_shared_schemas.json_types."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.json_types import as_json_object


def test_as_json_object_accepts_dict() -> None:
    payload = as_json_object({"key": "value"})

    assert payload["key"] == "value"


def test_as_json_object_rejects_non_object() -> None:
    with pytest.raises(TypeError, match="JSON object"):
        as_json_object(["not", "an", "object"])

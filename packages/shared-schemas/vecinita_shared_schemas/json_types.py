"""JSON-shaped value aliases for API payloads and audit blobs."""

from __future__ import annotations

from typing import TypeAlias, cast

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
# Top-level JSON objects from HTTP/DB; values are object until narrowed.
JsonObject: TypeAlias = dict[str, object]


def as_json_object(value: object) -> JsonObject:
    """Narrow an HTTP/JSON payload to a string-keyed object map."""
    if not isinstance(value, dict):
        msg = f"Expected JSON object, got {type(value).__name__}"
        raise TypeError(msg)
    return cast("JsonObject", value)

"""Typed JSON helpers for HTTP test responses (reportAny-safe)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

from vecinita_shared_schemas.json_types import JsonObject, as_json_object


class _JsonResponse(Protocol):
    def json(self) -> object: ...


def response_json_object(response: _JsonResponse) -> JsonObject:
    """Parse a FastAPI TestClient or httpx response body as JsonObject."""
    return as_json_object(cast(object, response.json()))


def header_str(headers: object, key: str, default: str = "") -> str:
    """Read a response header value as str (Starlette/httpx .get returns object)."""
    if not isinstance(headers, Mapping):
        msg = f"Expected mapping headers, got {type(headers).__name__}"
        raise TypeError(msg)
    value: object = headers.get(key, default)
    if value is None:
        return default
    return str(value)


def response_json_list(response: _JsonResponse) -> list[object]:
    """Parse a JSON array response body."""
    data: object = response.json()
    if not isinstance(data, list):
        msg = f"Expected JSON array, got {type(data).__name__}"
        raise TypeError(msg)
    return data


def json_str(obj: JsonObject, key: str) -> str:
    return str(obj[key])


def json_list(obj: JsonObject, key: str) -> list[object]:
    value = obj[key]
    if not isinstance(value, list):
        msg = f"Expected list at {key!r}, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def find_json_object_by_str(items: list[object], key: str, value: str) -> JsonObject:
    """Return the first JSON object in a list whose string field matches value."""
    for entry in items:
        obj = as_json_object(cast(object, entry))
        if key in obj and str(obj[key]) == value:
            return obj
    msg = f"No item with {key}={value!r} in list of {len(items)}"
    raise AssertionError(msg)


def json_int(obj: JsonObject, key: str) -> int:
    value = obj[key]
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def json_object_list(obj: JsonObject, key: str) -> list[JsonObject]:
    return json_object_items(obj[key])


def json_object_get(obj: JsonObject, key: str, *, default: JsonObject | None = None) -> JsonObject:
    fallback: object = {} if default is None else default
    return as_json_object(cast(object, obj.get(key, fallback)))


def json_object_items(raw: object) -> list[JsonObject]:
    """Narrow a JSON array of objects (e.g. browse/document list items)."""
    if not isinstance(raw, list):
        msg = f"Expected JSON array, got {type(raw).__name__}"
        raise TypeError(msg)
    items: list[JsonObject] = []
    for entry in raw:
        items.append(as_json_object(cast(object, entry)))
    return items

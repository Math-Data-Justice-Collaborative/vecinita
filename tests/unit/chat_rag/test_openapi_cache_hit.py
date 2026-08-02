"""T95.4: OpenAPI AskResponse documents cache_hit (F43 / M4 / S020-D15)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "chat-rag.yaml"

_CACHE_HIT_ENUM = frozenset({"none", "exact", "semantic", "retrieve"})


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def _ask_response_schema(spec: JsonObject) -> JsonObject:
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    return as_json_object(schemas["AskResponse"])


def test_openapi_ask_response_requires_cache_hit() -> None:
    """AskResponse requires cache_hit with F43 enum values."""
    schema = _ask_response_schema(_load_spec())
    required = cast("list[str]", schema["required"])
    assert "cache_hit" in required
    properties = as_json_object(schema["properties"])
    cache_hit = as_json_object(properties["cache_hit"])
    assert cache_hit["type"] == "string"
    assert set(cast("list[str]", cache_hit["enum"])) == _CACHE_HIT_ENUM


def test_openapi_ask_stream_documents_cache_hit_on_done() -> None:
    """ask/stream 200 description mentions cache_hit on done (api-contract)."""
    paths = as_json_object(_load_spec()["paths"])
    stream = as_json_object(paths["/ask/stream"])
    post = as_json_object(stream["post"])
    responses = as_json_object(post["responses"])
    ok = as_json_object(responses["200"])
    description = ok["description"]
    assert isinstance(description, str)
    assert "cache_hit" in description

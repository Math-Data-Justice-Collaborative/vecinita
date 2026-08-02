"""T103.2 — OpenAPI JobOptions.chunk_overlap_tokens (F49 / ADR-044)."""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "data-management.yaml"
_MAX_OVERLAP: Final[int] = 2047


def _job_options_props() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    spec = as_json_object(loaded)
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    job_options = as_json_object(schemas["JobOptions"])
    return as_json_object(job_options["properties"])


def test_openapi_job_options_chunk_overlap_tokens_field() -> None:
    """OpenAPI exposes chunk_overlap_tokens with F49 bounds."""
    props = _job_options_props()
    assert "chunk_overlap_tokens" in props
    field = as_json_object(props["chunk_overlap_tokens"])
    assert field.get("type") == "integer"
    assert field.get("minimum") == 0
    assert field.get("maximum") == _MAX_OVERLAP
    description = cast("str", field.get("description", ""))
    assert "32" in description
    assert "F49" in description or "ADR-044" in description

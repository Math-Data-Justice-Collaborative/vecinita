"""T88.5 - OpenAPI data-management JobOptions rebuild fields (F41 / RD-189-192)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "data-management.yaml"
_MAX_DOCUMENT_IDS = 1000


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def _job_options_props(spec: JsonObject) -> JsonObject:
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    job_options = as_json_object(schemas["JobOptions"])
    return as_json_object(job_options["properties"])


def test_openapi_job_options_rebuild_mode_enum() -> None:
    """JobOptions.mode must be reembed|rechunk|rescrape (RD-189)."""
    props = _job_options_props(_load_spec())
    assert "mode" in props
    mode = as_json_object(props["mode"])
    assert set(cast("list[str]", mode["enum"])) == {"reembed", "rechunk", "rescrape"}
    assert mode.get("nullable") is True


def test_openapi_job_options_rebuild_force_and_dry_run() -> None:
    """Force and dry_run are booleans defaulting false (RD-190/191)."""
    props = _job_options_props(_load_spec())
    for name in ("force", "dry_run"):
        assert name in props
        field = as_json_object(props[name])
        assert field.get("type") == "boolean"
        assert field.get("default") is False


def test_openapi_job_options_rebuild_document_ids_scope() -> None:
    """Optional document_ids scopes rebuild; omit = whole corpus (RD-192)."""
    props = _job_options_props(_load_spec())
    assert "document_ids" in props
    doc_ids = as_json_object(props["document_ids"])
    assert doc_ids.get("type") == "array"
    assert doc_ids.get("nullable") is True
    assert doc_ids.get("maxItems") == _MAX_DOCUMENT_IDS
    items = as_json_object(doc_ids["items"])
    assert items.get("format") == "uuid"


def test_openapi_job_type_includes_rebuild_and_urls_allow_empty() -> None:
    """job_type includes rebuild; CreateJobRequest urls may be empty (TC-161)."""
    spec = _load_spec()
    props = _job_options_props(spec)
    job_type = as_json_object(props["job_type"])
    assert "rebuild" in cast("list[str]", job_type["enum"])

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    create_req = as_json_object(schemas["CreateJobRequest"])
    create_props = as_json_object(create_req["properties"])
    urls = as_json_object(create_props["urls"])
    assert urls.get("minItems", 0) in (0, None)
    description = cast("str", urls.get("description", ""))
    assert "rebuild" in description.lower()


def test_openapi_job_options_backfill_fields_present() -> None:
    """Backfill flags remain on JobOptions (TP-S017-08; landed with rebuild)."""
    props = _job_options_props(_load_spec())
    assert "backfill" in props
    assert "backfill_source" in props
    source = as_json_object(props["backfill_source"])
    assert set(cast("list[str]", source["enum"])) == {"rescrape", "from_chunks"}
    assert "ack_reconstruct_from_chunks" in props

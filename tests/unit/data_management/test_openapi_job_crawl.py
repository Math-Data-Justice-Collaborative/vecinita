"""T109.4 — OpenAPI JobOptions crawl + GET /jobs/{job_id}/tree (F60 / TP3)."""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "data-management.yaml"
_DEFAULT_MAX_DEPTH: Final[int] = 2
_DEFAULT_MAX_PAGES: Final[int] = 25


def _spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def _job_options_props() -> JsonObject:
    components = as_json_object(_spec()["components"])
    schemas = as_json_object(components["schemas"])
    job_options = as_json_object(schemas["JobOptions"])
    return as_json_object(job_options["properties"])


def test_openapi_job_options_crawl_fields() -> None:
    """OpenAPI JobOptions documents crawl, max_depth, max_pages, crawl_scope."""
    props = _job_options_props()
    assert "crawl" in props
    crawl = as_json_object(props["crawl"])
    assert crawl.get("type") == "boolean"
    assert crawl.get("default") is False

    max_depth = as_json_object(props["max_depth"])
    assert max_depth.get("type") == "integer"
    assert max_depth.get("default") == _DEFAULT_MAX_DEPTH
    assert max_depth.get("minimum") == 0

    max_pages = as_json_object(props["max_pages"])
    assert max_pages.get("type") == "integer"
    assert max_pages.get("default") == _DEFAULT_MAX_PAGES
    assert max_pages.get("minimum") == 1

    scope = as_json_object(props["crawl_scope"])
    assert scope.get("default") == "same_domain"
    assert set(cast("list[object]", scope.get("enum", []))) == {
        "same_domain",
        "path_prefix",
    }


def test_openapi_job_metrics_crawl_counters() -> None:
    """JobMetrics MAY include crawl tallies (api-contract F60)."""
    components = as_json_object(_spec()["components"])
    schemas = as_json_object(components["schemas"])
    metrics = as_json_object(schemas["JobMetrics"])
    props = as_json_object(metrics["properties"])
    for key in ("pages_fetched", "pages_failed", "pages_skipped_robots", "crawl_stopped_reason"):
        assert key in props


def test_openapi_jobs_tree_path_and_schemas() -> None:
    """OpenAPI exposes GET /jobs/{job_id}/tree with TreeNode + JobTreeResponse."""
    paths = as_json_object(_spec()["paths"])
    assert "/jobs/{job_id}/tree" in paths
    tree_path = as_json_object(paths["/jobs/{job_id}/tree"])
    assert "get" in tree_path
    get_op = as_json_object(tree_path["get"])
    assert get_op.get("operationId") == "getJobTree"

    components = as_json_object(_spec()["components"])
    schemas = as_json_object(components["schemas"])
    assert "TreeNode" in schemas
    assert "JobTreeResponse" in schemas
    tree_node = as_json_object(schemas["TreeNode"])
    node_props = as_json_object(tree_node["properties"])
    assert set(cast("list[object]", as_json_object(node_props["kind"]).get("enum", []))) == {
        "domain",
        "path",
        "document",
        "chunk",
    }
    job_tree = as_json_object(schemas["JobTreeResponse"])
    required = cast("list[object]", job_tree.get("required", []))
    assert "job_id" in required
    assert "roots" in required

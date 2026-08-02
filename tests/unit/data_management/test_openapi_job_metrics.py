"""T104.2 - OpenAPI Job.metrics (F47-F48 / EV-019)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "data-management.yaml"


def test_openapi_job_metrics_schema() -> None:
    """Job exposes nullable metrics with skip/embed failure counters."""
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    spec = as_json_object(loaded)
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    assert "JobMetrics" in schemas
    job = as_json_object(schemas["Job"])
    props = as_json_object(job["properties"])
    assert "metrics" in props
    metrics_schema = as_json_object(schemas["JobMetrics"])
    metric_props = as_json_object(metrics_schema["properties"])
    assert "skipped_unchanged" in metric_props
    assert "urls_failed_embed" in metric_props

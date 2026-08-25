"""T130.2 - OpenAPI internal-write EV-027 automations / freshness / FT mirrors.

[Corpus: feature-list.md §F75-F77]
[Spec: docs/api-contract.md §EV-027]
[Spec: docs/sessions/S000-internal-docs-archive/execution-plan.md §T130.2]
[Spec: docs/adr/ADR-011-openapi-source-of-truth.md]
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "internal-write.yaml"


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def test_openapi_automations_config_and_runs_paths() -> None:
    """F75: GET/PATCH automations config + GET runs (api-contract EV-027)."""
    spec = _load_spec()
    paths = as_json_object(spec["paths"])
    assert "/automations/config" in paths
    config = as_json_object(paths["/automations/config"])
    assert "get" in config
    assert "patch" in config
    get_op = as_json_object(config["get"])
    assert get_op.get("operationId") == "getAutomationsConfig"
    patch_op = as_json_object(config["patch"])
    assert patch_op.get("operationId") == "patchAutomationsConfig"
    patch_body = as_json_object(as_json_object(patch_op["requestBody"])["content"])
    json_body = as_json_object(patch_body["application/json"])
    assert as_json_object(json_body["schema"]).get("$ref") == (
        "#/components/schemas/AutomationsConfigPatchRequest"
    )

    assert "/automations/runs" in paths
    runs = as_json_object(paths["/automations/runs"])
    assert "get" in runs
    assert as_json_object(runs["get"]).get("operationId") == "listAutomationRuns"
    assert "post" in runs
    post_op = as_json_object(runs["post"])
    assert post_op.get("operationId") == "createAutomationRun"
    post_body = as_json_object(as_json_object(post_op["requestBody"])["content"])
    json_body = as_json_object(post_body["application/json"])
    assert as_json_object(json_body["schema"]).get("$ref") == (
        "#/components/schemas/AutomationRunCreateRequest"
    )
    post_responses = as_json_object(post_op["responses"])
    assert "201" in post_responses

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    for name in (
        "AutomationsConfigResponse",
        "AutomationsConfigPatchRequest",
        "AutomationRun",
        "AutomationRunCreateRequest",
        "AutomationRunListResponse",
    ):
        assert name in schemas

    config_schema = as_json_object(schemas["AutomationsConfigResponse"])
    required = set(cast("list[str]", config_schema["required"]))
    assert required == {"enabled", "kill_switch", "max_concurrent"}

    run_schema = as_json_object(schemas["AutomationRun"])
    run_props = as_json_object(run_schema["properties"])
    job_type = as_json_object(run_props["job_type"])
    assert set(cast("list[str]", job_type["enum"])) == {
        "automation_catchup",
        "freshness_refresh",
    }


def test_openapi_freshness_refresh_and_document_fields() -> None:
    """F76: Refresh now path + stale list query + freshness document fields."""
    spec = _load_spec()
    paths = as_json_object(spec["paths"])
    assert "/documents/{document_id}/refresh" in paths
    refresh = as_json_object(paths["/documents/{document_id}/refresh"])
    post = as_json_object(refresh["post"])
    assert post.get("operationId") == "refreshDocument"
    responses = as_json_object(post["responses"])
    assert "200" in responses
    assert "404" in responses
    assert "409" in responses

    documents = as_json_object(paths["/documents"])
    get_docs = as_json_object(documents["get"])
    params = cast("list[object]", get_docs["parameters"])
    stale_param = next(
        (as_json_object(p) for p in params if as_json_object(p).get("name") == "stale"),
        None,
    )
    assert stale_param is not None
    assert stale_param.get("in") == "query"
    assert as_json_object(stale_param["schema"]).get("type") == "boolean"

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    summary = as_json_object(schemas["DocumentSummary"])
    summary_props = as_json_object(summary["properties"])
    for field in ("refresh_enabled", "last_checked_at", "stale"):
        assert field in summary_props

    patch_req = as_json_object(schemas["DocumentPatchRequest"])
    patch_props = as_json_object(patch_req["properties"])
    assert "refresh_enabled" in patch_props

    meta = as_json_object(schemas["DocumentMetadataResponse"])
    meta_props = as_json_object(meta["properties"])
    assert "refresh_enabled" in meta_props
    assert "last_checked_at" in meta_props


def test_openapi_finetune_eval_adapter_promote_paths() -> None:
    """F77: eval report + adapter pin GET + promote/rollback POST."""
    spec = _load_spec()
    paths = as_json_object(spec["paths"])
    assert "/finetune/runs/{run_id}/eval" in paths
    eval_path = as_json_object(paths["/finetune/runs/{run_id}/eval"])
    assert as_json_object(eval_path["get"]).get("operationId") == "getFinetuneEvalReport"

    assert "/finetune/adapter" in paths
    adapter = as_json_object(paths["/finetune/adapter"])
    assert as_json_object(adapter["get"]).get("operationId") == "getFinetuneAdapterPin"

    assert "/finetune/promote" in paths
    promote = as_json_object(paths["/finetune/promote"])
    post = as_json_object(promote["post"])
    assert post.get("operationId") == "promoteFinetuneAdapter"
    body = as_json_object(as_json_object(post["requestBody"])["content"])
    json_body = as_json_object(body["application/json"])
    assert as_json_object(json_body["schema"]).get("$ref") == (
        "#/components/schemas/FinetunePromoteRequest"
    )

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    for name in (
        "FinetuneEvalReportResponse",
        "FinetuneSideMetrics",
        "FinetunePromoteRequest",
        "FinetunePromoteResponse",
        "FinetuneAdapterPinResponse",
    ):
        assert name in schemas

    promote_resp = as_json_object(schemas["FinetunePromoteResponse"])
    required = set(cast("list[str]", promote_resp["required"]))
    assert {"promoted", "base", "auto_promote"}.issubset(required)
    props = as_json_object(promote_resp["properties"])
    assert as_json_object(props["auto_promote"]).get("enum") == [False]

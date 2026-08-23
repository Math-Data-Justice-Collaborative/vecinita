"""T129.6 — GET /internal/v1/finetune/runs/{id}/eval route (F77 / TC-261).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-261]
[Spec: docs/acceptance-criteria.md §AC-FT3]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from vecinita_internal_write_api.finetune_eval import get_finetune_eval_store
from vecinita_shared_schemas.finetune_eval import (
    FinetuneSideMetrics,
    build_finetune_eval_report,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import response_json_object
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

_BASE_FAITH = 0.7
_ADAPTER_FAITH = 0.72


def test_get_finetune_eval_route_ok_and_404(write_client: TestClient) -> None:
    """Write-API GET returns report for registered run; unknown → 404."""
    run_id = uuid4()
    missing = uuid4()
    store = get_finetune_eval_store()
    store.clear()
    store.put(
        build_finetune_eval_report(
            run_id=run_id,
            adapter_id="adapter-route",
            base_model_id="qwen2.5:1.5b-instruct",
            base=FinetuneSideMetrics(
                faithfulness=_BASE_FAITH,
                answer_relevancy=0.6,
                questions_scored=1,
            ),
            adapter=FinetuneSideMetrics(
                faithfulness=_ADAPTER_FAITH,
                answer_relevancy=0.65,
                questions_scored=1,
            ),
        )
    )

    ok = write_client.get(
        f"/internal/v1/finetune/runs/{run_id}/eval",
        headers=auth_headers(),
    )
    assert ok.status_code == HTTPStatus.OK
    body = response_json_object(ok)
    assert body["run_id"] == str(run_id)
    assert body["adapter_id"] == "adapter-route"
    assert body["auto_promote"] is False
    base = as_json_object(body["base"])
    adapter = as_json_object(body["adapter"])
    assert base["faithfulness"] == _BASE_FAITH
    assert adapter["faithfulness"] == _ADAPTER_FAITH

    missing_resp = write_client.get(
        f"/internal/v1/finetune/runs/{missing}/eval",
        headers=auth_headers(),
    )
    assert missing_resp.status_code == HTTPStatus.NOT_FOUND

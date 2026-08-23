"""UJ-082 / F77 — Approve FT train + human promote API e2e.

Drives DM ``/jobs`` (create → approve → train worker) and write-API finetune
eval/promote/rollback as one operator journey.

[Corpus: feature-list.md §F77]
[Corpus: user-journeys.md §UJ-082]
[Spec: docs/test-plan.md §TC-260 §TC-261 §TC-262 §TC-263 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT3 §AC-FT4 §AC-FT6 §AC-FT7 §AC-FT9]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

import os
from http import HTTPStatus
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.finetune_train import run_finetune_train_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_internal_write_api.finetune_eval import get_finetune_eval_store
from vecinita_internal_write_api.finetune_promote import get_finetune_adapter_pin_store
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.finetune import decide_prod_adapter_pin, parse_finetune_adapter_id
from vecinita_shared_schemas.finetune_eval import (
    HUMAN_JUDGMENT_SUMMARY,
    FinetuneSideMetrics,
    build_finetune_eval_report,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str, response_json_object

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"
_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_ADAPTER_ID = "adapter-uj082-e2e"
_BASE_MODEL = "qwen2.5:1.5b-instruct"
_BASE_FAITH = 0.7
_ADAPTER_FAITH = 0.72
_BASE_REL = 0.6
_ADAPTER_REL = 0.65
_QUESTIONS = 2
_PAIR_COUNT = 8


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _stub_train_invoker(_payload: dict[str, object]) -> dict[str, object]:
    return {
        "adapter_id": _ADAPTER_ID,
        "adapter_path": f"/adapters/{_ADAPTER_ID}",
        "pair_count": _PAIR_COUNT,
        "base_model_id": _BASE_MODEL,
    }


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture(autouse=True)
def _finetune_e2e_env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Isolate pin/eval stores and disable live auth JWKS for DM routes."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_ID", raising=False)
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", "1")
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "3")
    get_finetune_adapter_pin_store().clear()
    get_finetune_eval_store().clear()


def _dm_client(store: InMemoryJobStore) -> TestClient:
    """DM app with admin principal + stubbed FT train runner."""

    def runner(job_id: UUID) -> None:
        run_finetune_train_job(job_id, store=store, train_invoker=_stub_train_invoker)

    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=runner)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    return TestClient(app)


def test_uj082_approve_eval_promote_rollback_journey() -> None:  # noqa: PLR0915  # UJ journey covers TC-260-262 + TC-265
    """UJ-082: create, approve, eval, promote, rollback (TC-260/261/262/265)."""
    store = InMemoryJobStore()
    dm = _dm_client(store)
    write = TestClient(create_write_app())

    create = dm.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    assert create.status_code == HTTPStatus.ACCEPTED
    created = response_json_object(create)
    assert created["status"] == "pending"
    job_id = UUID(json_str(created, "job_id"))

    before_approve = dm.get(f"/jobs/{job_id}")
    assert before_approve.status_code == HTTPStatus.OK
    pending_body = response_json_object(before_approve)
    assert pending_body["status"] == "pending"
    assert pending_body["job_type"] == "finetune_train"
    assert pending_body["approved"] is False
    pending_record = store.get_job(job_id)
    assert pending_record is not None
    assert pending_record.status == "pending"

    pin0 = write.get("/internal/v1/finetune/adapter", headers=_auth())
    assert pin0.status_code == HTTPStatus.OK
    assert response_json_object(pin0) == {"adapter_id": None, "base": True}
    assert parse_finetune_adapter_id() is None
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=None,
            latest_adapter_id=_ADAPTER_ID,
        )
        is None
    )

    approve = dm.post(f"/jobs/{job_id}/approve")
    assert approve.status_code == HTTPStatus.OK
    approved_body = response_json_object(approve)
    assert approved_body["job_id"] == str(job_id)
    assert approved_body["approved"] is True
    assert approved_body["job_type"] == "finetune_train"

    after_train = dm.get(f"/jobs/{job_id}")
    assert after_train.status_code == HTTPStatus.OK
    trained = response_json_object(after_train)
    assert trained["status"] == "completed"
    assert trained["approved"] is True
    metrics = as_json_object(trained["metrics"])
    assert metrics["finetune_outcome"] == "trained"
    assert metrics["adapter_id"] == _ADAPTER_ID
    assert metrics["adapter_path"] == f"/adapters/{_ADAPTER_ID}"
    assert metrics["base_model_id"] == _BASE_MODEL
    assert metrics["pair_count"] == _PAIR_COUNT

    get_finetune_eval_store().put(
        build_finetune_eval_report(
            run_id=job_id,
            adapter_id=_ADAPTER_ID,
            base_model_id=_BASE_MODEL,
            base=FinetuneSideMetrics(
                faithfulness=_BASE_FAITH,
                answer_relevancy=_BASE_REL,
                questions_scored=_QUESTIONS,
            ),
            adapter=FinetuneSideMetrics(
                faithfulness=_ADAPTER_FAITH,
                answer_relevancy=_ADAPTER_REL,
                questions_scored=_QUESTIONS,
            ),
        )
    )

    eval_resp = write.get(f"/internal/v1/finetune/runs/{job_id}/eval", headers=_auth())
    assert eval_resp.status_code == HTTPStatus.OK
    report = response_json_object(eval_resp)
    assert report["run_id"] == str(job_id)
    assert report["adapter_id"] == _ADAPTER_ID
    assert report["base_model_id"] == _BASE_MODEL
    assert report["auto_promote"] is False
    assert report["summary"] == HUMAN_JUDGMENT_SUMMARY
    base = as_json_object(report["base"])
    adapter = as_json_object(report["adapter"])
    assert base == {
        "faithfulness": _BASE_FAITH,
        "answer_relevancy": _BASE_REL,
        "questions_scored": _QUESTIONS,
    }
    assert adapter == {
        "faithfulness": _ADAPTER_FAITH,
        "answer_relevancy": _ADAPTER_REL,
        "questions_scored": _QUESTIONS,
    }

    pin_before = write.get("/internal/v1/finetune/adapter", headers=_auth())
    assert response_json_object(pin_before) == {"adapter_id": None, "base": True}

    promote = write.post(
        "/internal/v1/finetune/promote",
        headers=_auth(),
        json={"adapter_id": _ADAPTER_ID},
    )
    assert promote.status_code == HTTPStatus.OK
    promote_body = response_json_object(promote)
    assert promote_body == {
        "promoted": True,
        "adapter_id": _ADAPTER_ID,
        "base": False,
        "auto_promote": False,
    }
    assert parse_finetune_adapter_id() == _ADAPTER_ID
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id="adapter-other-on-volume",
        )
        == _ADAPTER_ID
    )

    pin_after = write.get("/internal/v1/finetune/adapter", headers=_auth())
    assert response_json_object(pin_after) == {
        "adapter_id": _ADAPTER_ID,
        "base": False,
    }

    rollback = write.post(
        "/internal/v1/finetune/promote",
        headers=_auth(),
        json={"rollback": True},
    )
    assert rollback.status_code == HTTPStatus.OK
    assert response_json_object(rollback) == {
        "promoted": False,
        "adapter_id": None,
        "base": True,
        "auto_promote": False,
    }
    assert parse_finetune_adapter_id() is None
    pin_rolled = write.get("/internal/v1/finetune/adapter", headers=_auth())
    assert response_json_object(pin_rolled) == {"adapter_id": None, "base": True}


def test_uj082_kill_switch_blocks_train_after_approve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-263: kill-switch on — approve schedules runner but GPU train is skipped."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    dm = _dm_client(store)

    create = dm.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))

    approve = dm.post(f"/jobs/{job_id}/approve")
    assert approve.status_code == HTTPStatus.OK
    assert response_json_object(approve)["approved"] is True

    after = dm.get(f"/jobs/{job_id}")
    assert after.status_code == HTTPStatus.OK
    body = response_json_object(after)
    assert body["status"] == "completed"
    assert body["approved"] is True
    metrics = as_json_object(body["metrics"])
    assert metrics["finetune_outcome"] == "skip_kill_switch"
    assert metrics["adapter_id"] is None


def test_uj082_daily_cap_blocks_train_after_approve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-263: daily FT cap — approved train completes with skip_daily_cap."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "1")
    store = InMemoryJobStore()
    prior = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": True},
    )
    store.update_job(
        prior.job_id,
        status="completed",
        metrics={"finetune_outcome": "trained", "adapter_id": "prior"},
    )

    dm = _dm_client(store)
    create = dm.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    assert dm.post(f"/jobs/{job_id}/approve").status_code == HTTPStatus.OK

    after = response_json_object(dm.get(f"/jobs/{job_id}"))
    assert after["status"] == "completed"
    metrics = as_json_object(after["metrics"])
    assert metrics["finetune_outcome"] == "skip_daily_cap"
    assert metrics["adapter_id"] is None


def test_uj082_create_without_approve_does_not_start_gpu() -> None:
    """TC-260: create alone leaves pending; runner never invoked."""
    store = InMemoryJobStore()
    started: list[UUID] = []

    def runner(job_id: UUID) -> None:
        started.append(job_id)
        run_finetune_train_job(job_id, store=store, train_invoker=_stub_train_invoker)

    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=runner)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    dm = TestClient(app)

    create = dm.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    body = response_json_object(dm.get(f"/jobs/{job_id}"))
    assert body["status"] == "pending"
    assert body["approved"] is False
    assert started == []

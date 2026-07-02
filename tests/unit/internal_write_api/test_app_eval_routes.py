"""Unit tests for eval HTTP routes on internal write API (F36, ADR-034)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from vecinita_eval.runner import EvalSummary
from vecinita_internal_write_api.eval_service import create_eval_run
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.internal_write import EvalRunCreateRequest

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_int, json_str, response_json_object
from tests.helpers.ollama_models_mock import MockOllamaModelsClient
from tests.unit.internal_write_api.conftest import auth_headers, database_url
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)
from vecinita_internal_write_api.ollama_models_client import OllamaModelsClientError
from vecinita_shared_schemas.ollama_models import (
    OllamaModelListResponse,
    OllamaModelPullResponse,
)

_MAX_EVAL_PAGE_SIZE = 100

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@pytest.fixture
def eval_write_client(internal_api_env: None) -> TestClient:
    """TestClient with eval harness dependencies injected."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    return TestClient(
        create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()),
    )


def test_create_eval_run_route_accepts_empty_body(eval_write_client: TestClient) -> None:
    """POST /eval/runs defaults corpus_profile and schedules background execution."""
    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = eval_write_client.post(
            "/internal/v1/eval/runs",
            headers=auth_headers(),
        )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert json_str(body, "status") == "pending"


def test_factory_create_app_wires_default_eval_judge_from_env(
    internal_api_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_app() without eval_judge must still pass a judge when Modal LLM URL is set."""
    _ = internal_api_env
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app(eval_embed_fn=eval_embed_fn))
    with patch(
        "vecinita_internal_write_api.eval_service.run_golden_eval",
        return_value=(
            [],
            EvalSummary(
                retrieval_relevance=0.0,
                faithfulness=None,
                answer_relevancy=None,
                latency_p95_ms=1,
            ),
        ),
    ) as mock_run:
        response = client.post(
            "/internal/v1/eval/runs",
            json={"corpus_profile": "fixture"},
            headers=auth_headers(),
        )
    assert response.status_code == HTTPStatus.ACCEPTED
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["judge"] is not None
    assert mock_run.call_args.kwargs["llm"] is not None


def test_list_eval_runs_clamps_pagination(eval_write_client: TestClient) -> None:
    """GET /eval/runs clamps page and page_size to supported bounds."""
    response = eval_write_client.get(
        "/internal/v1/eval/runs",
        params={"page": 0, "page_size": 500},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "page") == 1
    assert json_int(body, "page_size") == _MAX_EVAL_PAGE_SIZE


def test_get_eval_timeseries_clamps_limit(eval_write_client: TestClient) -> None:
    """GET /eval/runs/timeseries clamps limit between 1 and 500."""
    low = eval_write_client.get(
        "/internal/v1/eval/runs/timeseries",
        params={"limit": 0},
        headers=auth_headers(),
    )
    high = eval_write_client.get(
        "/internal/v1/eval/runs/timeseries",
        params={"limit": 999},
        headers=auth_headers(),
    )
    assert low.status_code == HTTPStatus.OK
    assert high.status_code == HTTPStatus.OK


def test_get_eval_run_route_returns_404(eval_write_client: TestClient) -> None:
    """GET /eval/runs/{id} returns 404 for unknown ids."""
    response = eval_write_client.get(
        f"/internal/v1/eval/runs/{uuid4()}",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_eval_criteria_crud_and_patch_404(eval_write_client: TestClient) -> None:
    """Criteria list/create succeed; PATCH unknown id returns 404."""
    slug = f"unit-criterion-{uuid4().hex[:8]}"
    create = eval_write_client.post(
        "/internal/v1/eval/criteria",
        json={
            "slug": slug,
            "label": "Unit criterion",
            "rubric": "Score the answer.",
            "scorer_type": "llm_rubric",
            "enabled": True,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.CREATED
    criterion_id = json_str(response_json_object(create), "criterion_id")

    listing = eval_write_client.get(
        "/internal/v1/eval/criteria",
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK

    patch = eval_write_client.patch(
        f"/internal/v1/eval/criteria/{criterion_id}",
        json={"enabled": False},
        headers=auth_headers(),
    )
    assert patch.status_code == HTTPStatus.OK

    missing = eval_write_client.patch(
        f"/internal/v1/eval/criteria/{uuid4()}",
        json={"enabled": True},
        headers=auth_headers(),
    )
    assert missing.status_code == HTTPStatus.NOT_FOUND


def test_get_eval_run_route_returns_detail(
    engine: Engine,
    eval_write_client: TestClient,
) -> None:
    """GET /eval/runs/{id} returns persisted run detail."""
    created = create_eval_run(
        engine,
        body=EvalRunCreateRequest(corpus_profile="fixture"),
        requester_id=uuid4(),
    )
    try:
        response = eval_write_client.get(
            f"/internal/v1/eval/runs/{created.response.run_id}",
            headers=auth_headers(),
        )
        assert response.status_code == HTTPStatus.OK
        body = response_json_object(response)
        assert json_str(body, "status") == "pending"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": created.response.run_id},
            )
            conn.execute(
                text("DELETE FROM eval_runs WHERE id = :id"),
                {"id": created.response.run_id},
            )


def test_ingest_audit_event_rejects_operator_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /audit/event rejects operator JWTs (service key only)."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key, internal_api_key="test-internal-key"))

    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app())
    token = sign_test_jwt(private_key, role="admin")
    try:
        response = client.post(
            "/internal/v1/audit/event",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "event_type": "user.invited",
                "entity_type": "user",
                "entity_id": str(uuid4()),
                "payload": {},
            },
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
    finally:
        reset_auth_config_for_tests()


def test_eval_config_preset_routes_require_operator_jwt(
    eval_write_client: TestClient,
) -> None:
    """Preset routes reject the service key because owner_id is required."""
    preset_id = uuid4()
    assert (
        eval_write_client.get(
            "/internal/v1/eval/config-presets",
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        eval_write_client.post(
            "/internal/v1/eval/config-presets",
            json={"name": "x", "config": {}},
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        eval_write_client.get(
            f"/internal/v1/eval/config-presets/{preset_id}",
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        eval_write_client.patch(
            f"/internal/v1/eval/config-presets/{preset_id}",
            json={"name": "y"},
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        eval_write_client.post(
            f"/internal/v1/eval/config-presets/{preset_id}/clone",
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.FORBIDDEN
    )


def test_eval_config_preset_routes_return_404_for_missing_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preset GET/PATCH/clone return 404 when the preset id does not exist."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()))
    token = sign_test_jwt(private_key, role="admin")
    missing = uuid4()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        assert (
            client.get(
                f"/internal/v1/eval/config-presets/{missing}",
                headers=headers,
            ).status_code
            == HTTPStatus.NOT_FOUND
        )
        assert (
            client.patch(
                f"/internal/v1/eval/config-presets/{missing}",
                json={"name": "missing"},
                headers=headers,
            ).status_code
            == HTTPStatus.NOT_FOUND
        )
        assert (
            client.post(
                f"/internal/v1/eval/config-presets/{missing}/clone",
                headers=headers,
            ).status_code
            == HTTPStatus.NOT_FOUND
        )
    finally:
        reset_auth_config_for_tests()


def test_ollama_model_routes_require_configured_client(
    eval_write_client: TestClient,
) -> None:
    """Ollama list/pull return 503 when no client is wired."""
    assert (
        eval_write_client.get(
            "/internal/v1/models/ollama",
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.SERVICE_UNAVAILABLE
    )
    assert (
        eval_write_client.post(
            "/internal/v1/models/ollama/pull",
            json={"model_id": "qwen2.5:1.5b-instruct"},
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.SERVICE_UNAVAILABLE
    )


class _FailingOllamaClient:
    def list_models(self) -> OllamaModelListResponse:
        msg = "upstream down"
        raise OllamaModelsClientError(msg)

    def start_pull(self, model_id: str) -> OllamaModelPullResponse:
        msg = "pull upstream down"
        raise OllamaModelsClientError(msg)

    def close(self) -> None:
        return None


def test_ollama_model_routes_map_client_errors_to_502(
    internal_api_env: None,
) -> None:
    """Ollama routes translate OllamaModelsClientError to 502."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(
        create_app(
            eval_embed_fn=eval_embed_fn,
            eval_judge=MockEvalJudge(),
            ollama_models_client=_FailingOllamaClient(),
        )
    )
    assert (
        client.get(
            "/internal/v1/models/ollama",
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.BAD_GATEWAY
    )
    assert (
        client.post(
            "/internal/v1/models/ollama/pull",
            json={"model_id": "qwen2.5:1.5b-instruct"},
            headers=auth_headers(),
        ).status_code
        == HTTPStatus.BAD_GATEWAY
    )


def test_ollama_model_routes_delegate_to_injected_client(
    internal_api_env: None,
) -> None:
    """Ollama list/pull succeed when a mock client is injected."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    mock_client = MockOllamaModelsClient()
    client = TestClient(
        create_app(
            eval_embed_fn=eval_embed_fn,
            eval_judge=MockEvalJudge(),
            ollama_models_client=mock_client,
        )
    )
    listing = client.get(
        "/internal/v1/models/ollama",
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK
    pull = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": "llama3.2:3b"},
        headers=auth_headers(),
    )
    assert pull.status_code == HTTPStatus.ACCEPTED
    assert mock_client.pull_requests == ["llama3.2:3b"]


def test_eval_config_preset_routes_with_admin_jwt(
    monkeypatch: pytest.MonkeyPatch,
    engine: Engine,
) -> None:
    """Preset CRUD routes succeed for authenticated admin JWTs."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()))
    owner_id = uuid4()
    token = sign_test_jwt(private_key, sub=owner_id, role="admin")
    headers = {"Authorization": f"Bearer {token}"}
    preset_id: UUID | None = None
    try:
        create = client.post(
            "/internal/v1/eval/config-presets",
            json={"name": "route-preset", "config": {"top_k": 6}, "shared": False},
            headers=headers,
        )
        assert create.status_code == HTTPStatus.CREATED
        preset_id = UUID(json_str(response_json_object(create), "preset_id"))

        listing = client.get(
            "/internal/v1/eval/config-presets",
            headers=headers,
        )
        assert listing.status_code == HTTPStatus.OK

        fetched = client.get(
            f"/internal/v1/eval/config-presets/{preset_id}",
            headers=headers,
        )
        assert fetched.status_code == HTTPStatus.OK

        patched = client.patch(
            f"/internal/v1/eval/config-presets/{preset_id}",
            json={"name": "route-preset-v2"},
            headers=headers,
        )
        assert patched.status_code == HTTPStatus.OK
        assert json_str(response_json_object(patched), "name") == "route-preset-v2"
    finally:
        reset_auth_config_for_tests()
        if preset_id is not None:
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM eval_config_presets WHERE id = :id"),
                    {"id": preset_id},
                )


def test_create_eval_run_with_preset_requires_operator_jwt(
    eval_write_client: TestClient,
) -> None:
    """POST /eval/runs rejects preset_id when only the service key is provided."""
    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = eval_write_client.post(
            "/internal/v1/eval/runs",
            json={"preset_id": str(uuid4())},
            headers=auth_headers(),
        )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_ingest_audit_event_service_key(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /audit/event accepts the internal service key and returns 202."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key, internal_api_key="test-internal-key"))

    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app())
    entity_id = uuid4()
    try:
        response = client.post(
            "/internal/v1/audit/event",
            headers=auth_headers(),
            json={
                "event_type": "user.invited",
                "entity_type": "user",
                "entity_id": str(entity_id),
                "payload": {"role": "viewer"},
            },
        )
        assert response.status_code == HTTPStatus.ACCEPTED
    finally:
        reset_auth_config_for_tests()
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM audit_log WHERE entity_id = :id"),
                {"id": entity_id},
            )

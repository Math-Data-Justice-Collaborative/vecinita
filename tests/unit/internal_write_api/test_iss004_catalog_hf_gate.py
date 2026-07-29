"""ISS-004 — catalog family tags filtered through resolve_hf_repo (unit / branch coverage)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.json_types import as_json_object

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_list, json_str, response_json_object
from tests.helpers.playground_library_mock import MockPlaygroundLibraryClient
from tests.helpers.playground_models_mock import MockPlaygroundModelsClient
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey


@pytest.fixture
def catalog_gate_client(
    internal_api_env: None,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey]]:
    """Write API with mocked library returning allowed + NC-blocked tags."""
    _ = internal_api_env
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    set_auth_config_for_tests(make_auth_config(private_key))
    mock_library = MockPlaygroundLibraryClient()
    mock_library.tags_by_slug["qwen2.5"] = [
        "qwen2.5:1.5b-instruct",  # allowed → try succeeds
        "qwen2.5:3b-instruct",  # NC blocked → ValueError continue
        "totally-unknown:tag",  # unmapped → ValueError continue
    ]
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    app = create_app(
        eval_embed_fn=eval_embed_fn,
        eval_judge=MockEvalJudge(),
        playground_models_client=MockPlaygroundModelsClient(),
        playground_library_client=mock_library,
    )
    with TestClient(app) as client:
        yield client, private_key
    reset_auth_config_for_tests()


def test_catalog_family_tags_filters_nc_and_unmapped(
    catalog_gate_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """GET catalog/{slug} keeps resolve_hf_repo-ok tags only (ISS-004 / RD-168)."""
    client, private_key = catalog_gate_client
    token = sign_test_jwt(private_key, role="super-admin")
    response = client.get(
        "/internal/v1/models/ollama/catalog/qwen2.5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "slug") == "qwen2.5"
    model_ids = [as_json_object(row).get("model_id") for row in json_list(body, "tags")]
    assert model_ids == ["qwen2.5:1.5b-instruct"]

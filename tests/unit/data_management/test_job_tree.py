"""T109.4 — GET /jobs/{job_id}/tree nested result nodes (F60 / api-contract)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Final
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_EXPECTED_DOMAINS: Final[int] = 2
_EXPECTED_DOCS_UNDER_PATH: Final[int] = 2


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow route tests without a live Supabase JWKS."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def _client(store: InMemoryJobStore) -> TestClient:
    app = create_app(store=store, require_proxy_auth=False)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    return TestClient(app)


def test_get_job_tree_returns_nested_domain_path_document() -> None:
    """GET /jobs/{id}/tree nests domain → path → document from job URLs."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[
            "https://example.com/docs/a.html",
            "https://example.com/docs/b.html",
            "https://other.org/index.html",
        ],
        options={"crawl": True, "max_depth": 2, "max_pages": 25},
    )
    store.update_job(record.job_id, status="completed")
    client = _client(store)

    response = client.get(f"/jobs/{record.job_id}/tree")

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "job_id") == str(record.job_id)
    roots = json_list(body, "roots")
    assert len(roots) == _EXPECTED_DOMAINS
    domains = {json_str(as_json_object(root), "label") for root in roots}
    assert domains == {"example.com", "other.org"}
    example = next(
        as_json_object(root)
        for root in roots
        if json_str(as_json_object(root), "label") == "example.com"
    )
    assert json_str(example, "kind") == "domain"
    path_children = json_list(example, "children")
    assert len(path_children) >= 1
    docs_path = as_json_object(path_children[0])
    assert json_str(docs_path, "kind") == "path"
    assert json_str(docs_path, "label") == "docs"
    documents = json_list(docs_path, "children")
    assert len(documents) == _EXPECTED_DOCS_UNDER_PATH
    for doc in documents:
        node = as_json_object(doc)
        assert json_str(node, "kind") == "document"
        assert "url" in node
        assert json_str(node, "status") == "completed"


def test_get_job_tree_404_when_unknown() -> None:
    """Unknown job_id yields 404."""
    client = _client(InMemoryJobStore())
    response = client.get(f"/jobs/{uuid4()}/tree")
    assert response.status_code == HTTPStatus.NOT_FOUND

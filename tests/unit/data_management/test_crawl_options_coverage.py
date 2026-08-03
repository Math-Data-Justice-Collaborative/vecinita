"""Coverage for crawl option parsing and root-URL job trees — EV-022."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.job_tree import build_job_tree
from vecinita_data_management_backend.pipeline import (
    _option_int,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_data_management_backend.store import InMemoryJobStore, JobRecord
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")
_OPTION_INT = 3
_OPTION_STR = 7
_OPTION_FALLBACK_BOOL = 9
_OPTION_FALLBACK_FLOAT = 4
_OPTION_MISSING = 2
_MAX_DEPTH = 2
_MAX_PAGES = 10


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def test_option_int_bool_str_and_fallback() -> None:
    """_option_int accepts int/str and falls back for bool/other types."""
    assert _option_int({"n": _OPTION_INT}, "n", 1) == _OPTION_INT
    assert _option_int({"n": str(_OPTION_STR)}, "n", 1) == _OPTION_STR
    assert _option_int({"n": True}, "n", _OPTION_FALLBACK_BOOL) == _OPTION_FALLBACK_BOOL
    assert _option_int({"n": 1.5}, "n", _OPTION_FALLBACK_FLOAT) == _OPTION_FALLBACK_FLOAT
    assert _option_int({}, "n", _OPTION_MISSING) == _OPTION_MISSING


def test_build_job_tree_root_url_uses_slash_document_label() -> None:
    """Root URL with no path segments labels the document '/'."""
    record = JobRecord(
        job_id=UUID("22222222-2222-4222-8222-222222222222"),
        status="completed",
        urls=["https://example.com"],
        options={},
    )
    tree = build_job_tree(record)
    assert len(tree.roots) == 1
    domain = tree.roots[0]
    assert domain.label == "example.com"
    assert domain.children is not None
    assert len(domain.children) == 1
    doc = domain.children[0]
    assert doc.kind == "document"
    assert doc.label == "/"


def test_create_job_persists_crawl_options() -> None:
    """POST /jobs with crawl options stores crawl/max_depth/max_pages/scope."""
    store = InMemoryJobStore()
    app = create_app(store=store, require_proxy_auth=False)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/seed"],
            "options": {
                "chunk_size_tokens": 256,
                "crawl": True,
                "max_depth": _MAX_DEPTH,
                "max_pages": _MAX_PAGES,
                "crawl_scope": "same_domain",
            },
        },
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    job_id = json_str(body, "job_id")
    record = store.get_job(UUID(job_id))
    assert record is not None
    assert record.options.get("crawl") is True
    assert record.options.get("max_depth") == _MAX_DEPTH
    assert record.options.get("max_pages") == _MAX_PAGES
    assert record.options.get("crawl_scope") == "same_domain"

    tree_resp = client.get(f"/jobs/{job_id}/tree")
    assert tree_resp.status_code == HTTPStatus.OK
    roots = json_list(response_json_object(tree_resp), "roots")
    assert roots
    assert json_str(as_json_object(roots[0]), "kind") == "domain"

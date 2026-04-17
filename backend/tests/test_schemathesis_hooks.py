"""Unit tests for Schemathesis hook helpers (gateway live CLI stability)."""

from __future__ import annotations

import pytest

import tests.schemathesis_hooks as sh

pytestmark = pytest.mark.unit


def test_map_body_normalizes_scrape_post(monkeypatch):
    class Op:
        path = "/api/v1/scrape"
        method = "post"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SCRAPE_URL", "https://vecinita.example/doc")
    body = sh.map_body(Ctx(), {"urls": ["https://bad"], "force_loader": "playwright"})
    assert body == {
        "urls": ["https://vecinita.example/doc"],
        "force_loader": "auto",
        "stream": False,
    }


def test_map_query_sets_source_url(monkeypatch):
    class Op:
        path = "/api/v1/documents/preview"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SOURCE_URL", "https://db.example/a")
    q = sh.map_query(Ctx(), {"source_url": "x", "limit": 2})
    assert q["source_url"] == "https://db.example/a"
    assert q["limit"] == 2


def test_map_path_parameters_sets_job_id(monkeypatch):
    class Op:
        path = "/api/v1/scrape/{job_id}"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SCRAPE_JOB_ID", "11111111-2222-3333-4444-555555555555")
    pp = sh.map_path_parameters(Ctx(), {"job_id": "bad"})
    assert pp["job_id"] == "11111111-2222-3333-4444-555555555555"


def test_map_path_parameters_modal_registry_gateway_job_id(monkeypatch):
    class Op:
        path = "/api/v1/modal-jobs/registry/{gateway_job_id}"
        method = "delete"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_MODAL_GATEWAY_JOB_ID", "aaaaaaaa-bbbb-cccc-dddd-000000000001")
    pp = sh.map_path_parameters(Ctx(), {"gateway_job_id": "bad"})
    assert pp["gateway_job_id"] == "aaaaaaaa-bbbb-cccc-dddd-000000000001"


def test_map_query_modal_scraper_list_drops_null_user_id():
    class Op:
        path = "/api/v1/modal-jobs/scraper"
        method = "get"

    class Ctx:
        operation = Op()

    q = sh.map_query(Ctx(), {"user_id": "null", "limit": 10})
    assert "user_id" not in q
    assert q["limit"] == 10


def test_map_path_parameters_accepts_none_stateful(monkeypatch):
    """Stateful generation may pass None; we still inject a stable job_id."""

    class Op:
        path = "/api/v1/scrape/{job_id}"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SCRAPE_JOB_ID", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    pp = sh.map_path_parameters(Ctx(), None)
    assert pp["job_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_map_query_accepts_none_for_documents_paths(monkeypatch):
    class Op:
        path = "/api/v1/documents/preview"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SOURCE_URL", "https://seed.example/doc")
    q = sh.map_query(Ctx(), None)
    assert q["source_url"] == "https://seed.example/doc"

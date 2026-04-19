"""Unit tests for Schemathesis hook helpers (gateway live CLI stability)."""

from __future__ import annotations

import logging

import pytest
from schemathesis import HookContext
from schemathesis.checks import CheckResult
from schemathesis.core.failures import ServerError
from schemathesis.engine import Status

import tests.schemathesis_hooks as sh

pytestmark = pytest.mark.unit


def test_map_body_data_management_submit_job(monkeypatch):
    class Op:
        path = "/jobs"
        method = "post"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_DM_SUBMIT_URL", "https://vecinita.example/job")
    monkeypatch.setenv("SCHEMATHESIS_DM_USER_ID", "operator-99")
    body = sh.map_body(Ctx(), {"url": "https://bad", "user_id": "x"})
    assert body == {"url": "https://vecinita.example/job", "user_id": "operator-99"}


def test_map_query_data_management_list_jobs():
    class Op:
        path = "/jobs"
        method = "get"

    class Ctx:
        operation = Op()

    q = sh.map_query(Ctx(), {"limit": 99, "user_id": "null"})
    assert q == {"limit": 10}


def test_map_path_parameters_data_management_job_id(monkeypatch):
    class Op:
        path = "/jobs/{job_id}/cancel"
        method = "post"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_DM_JOB_ID", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    pp = sh.map_path_parameters(Ctx(), {"job_id": "bad"})
    assert pp["job_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


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
    assert q["limit"] == 3


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


def test_map_query_sets_stream_question(monkeypatch):
    class Op:
        path = "/api/v1/ask/stream"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_STREAM_QUESTION", "Ping")
    q = sh.map_query(Ctx(), {"lang": "en"})
    assert q["question"] == "Ping"
    assert q["lang"] == "en"


def test_map_query_ask_stable_bundle(monkeypatch):
    class Op:
        path = "/api/v1/ask"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_ASK_QUESTION", "Ping ask")
    q = sh.map_query(Ctx(), {"question": "ignored", "tag_match_mode": "all"})
    assert q == {
        "question": "Ping ask",
        "tag_match_mode": "any",
        "include_untagged_fallback": True,
        "rerank": False,
        "rerank_top_k": 10,
    }


def test_before_call_strips_schemathesis_probe_query_keys():
    class Op:
        path = "/api/v1/ask"
        method = "get"

    class Case:
        query = {"question": "q", "X-Schemathesis-Probe": "1", "x-schemathesis-other": "2"}

    class Ctx:
        operation = Op()

    sh.before_call(Ctx(), Case(), {})
    assert Case.query == {"question": "q"}


def test_map_query_accepts_none_for_documents_paths(monkeypatch):
    class Op:
        path = "/api/v1/documents/preview"
        method = "get"

    class Ctx:
        operation = Op()

    monkeypatch.setenv("SCHEMATHESIS_SOURCE_URL", "https://seed.example/doc")
    q = sh.map_query(Ctx(), None)
    assert q["source_url"] == "https://seed.example/doc"
    assert q["limit"] == 3


def test_map_query_documents_per_path_source_url_overrides(monkeypatch):
    class Prev:
        path = "/api/v1/documents/preview"
        method = "get"

    class Dl:
        path = "/api/v1/documents/download-url"
        method = "get"

    class Ctx:
        def __init__(self, op):
            self.operation = op

    monkeypatch.setenv("SCHEMATHESIS_SOURCE_URL", "https://default.example/a")
    monkeypatch.setenv("SCHEMATHESIS_DOCUMENTS_PREVIEW_SOURCE_URL", "https://preview.example/p")
    monkeypatch.setenv("SCHEMATHESIS_DOCUMENTS_DOWNLOAD_SOURCE_URL", "https://download.example/d")
    qp = sh.map_query(Ctx(Prev()), None)
    assert qp["source_url"] == "https://preview.example/p"
    qd = sh.map_query(Ctx(Dl()), None)
    assert qd["source_url"] == "https://download.example/d"


def test_before_after_load_schema_verbose_logs(monkeypatch, caplog):
    monkeypatch.setenv("SCHEMATHESIS_HOOKS_VERBOSE", "1")
    caplog.set_level(logging.INFO)
    raw: dict = {
        "openapi": "3.0.0",
        "info": {"title": "Unit API", "version": "9"},
        "paths": {"/p": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    sh.before_load_schema(HookContext(), raw)
    assert "before_load_schema" in caplog.text
    assert "Unit API" in caplog.text

    class _Cnt:
        def __init__(self, total: int, selected: int) -> None:
            self.total = total
            self.selected = selected

    class _Stat:
        def __init__(self) -> None:
            self.operations = _Cnt(3, 2)
            self.links = _Cnt(0, 0)

    class FakeSchema:
        raw_schema = raw
        location = "https://example/openapi.json"
        statistic = _Stat()

    sh.after_load_schema(HookContext(), FakeSchema())
    assert "after_load_schema" in caplog.text


def test_after_call_and_after_validate_noop():
    sh.after_call(HookContext(), None, None)
    sh.after_validate(HookContext(), None, None, [])


def test_after_validate_logs_failures_when_verbose(monkeypatch, caplog):
    monkeypatch.setenv("SCHEMATHESIS_HOOKS_VERBOSE", "1")
    caplog.set_level(logging.WARNING)
    res = CheckResult(
        name="not_a_server_error",
        status=Status.FAILURE,
        failure=ServerError(operation="GET /x", status_code=500),
    )
    sh.after_validate(HookContext(), None, None, [res])
    assert "not_a_server_error" in caplog.text

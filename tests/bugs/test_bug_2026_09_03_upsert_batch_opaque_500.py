"""BUG-2026-09-03 — batch upsert must not return opaque Internal Server Error.

[Spec: docs/bug-reports/BUG-2026-09-03-upsert-batch-opaque-500.md]
[Corpus: feature-list.md §F79]

Full suite: tests/unit/internal_write_api/test_batch_upsert_error_detail.py
"""

from __future__ import annotations

import logging
import os
import uuid
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str, response_json_object

_WRITE_KEY = "test-internal-key"


@pytest.fixture
def write_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Write API TestClient with service bearer auth."""
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _WRITE_KEY)
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )
    client = TestClient(create_write_app())
    client.headers.update({"Authorization": f"Bearer {_WRITE_KEY}"})
    return client


def test_bug_2026_09_03_batch_upsert_returns_stable_error_code_on_failure(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Layer guard: opaque 500 body is replaced with stable error_code."""

    def _boom(**_kwargs: object) -> object:
        msg = "simulated db failure"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "vecinita_internal_write_api.routes.documents.batch_upsert_documents",
        _boom,
    )
    with caplog.at_level(logging.ERROR):
        response = write_client.post(
            "/internal/v1/documents/batch",
            json={
                "documents": [
                    {
                        "url": f"https://opaque-500-{uuid.uuid4().hex[:8]}.example.com/",
                        "title": "boom",
                        "language": "en",
                        "content_hash": "abc",
                        "body_text": "x",
                        "chunks": [],
                    }
                ]
            },
        )
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    detail = as_json_object(response_json_object(response)["detail"])
    assert json_str(detail, "error_code") == "batch_upsert_failed"
    assert json_str(detail, "error_type") == "RuntimeError"
    assert "simulated db failure" not in str(detail)
    assert any("batch_upsert failed" in r.message for r in caplog.records)


def test_bug_2026_09_03_batch_upsert_maps_integrity_error_code(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Layer guard: IntegrityError maps to batch_upsert_integrity_error."""

    def _boom(**_kwargs: object) -> object:
        statement = "INSERT"
        raise IntegrityError(statement, {}, Exception("duplicate"))

    monkeypatch.setattr(
        "vecinita_internal_write_api.routes.documents.batch_upsert_documents",
        _boom,
    )
    response = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": f"https://integrity-{uuid.uuid4().hex[:8]}.example.com/",
                    "title": "boom",
                    "language": "en",
                    "content_hash": "abc",
                    "body_text": "x",
                    "chunks": [],
                }
            ]
        },
    )
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    detail = as_json_object(response_json_object(response)["detail"])
    assert json_str(detail, "error_code") == "batch_upsert_integrity_error"
    assert json_str(detail, "error_type") == "IntegrityError"

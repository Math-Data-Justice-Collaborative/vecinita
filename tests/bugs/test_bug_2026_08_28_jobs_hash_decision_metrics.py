"""BUG-2026-08-28: GET /jobs 500 when Job metrics include freshness hash_decision.

Live Modal: ValidationError metrics.hash_decision Extra inputs are not permitted.
Freshness worker writes hash_decision; JobMetrics must accept it (F79 / F32).
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore, job_record_to_schema
from vecinita_shared_schemas.data_management import JobMetrics
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    json_str,
    response_json_object,
)


def test_job_metrics_accepts_hash_decision_skip_rechunk() -> None:
    """Schema contract: hash_decision from freshness_refresh must validate (F79)."""
    metrics = JobMetrics.model_validate(
        {
            "freshness_outcome": "verified_unchanged",
            "documents_processed": 1,
            "hash_decision": "skip_rechunk",
        }
    )
    assert metrics.hash_decision == "skip_rechunk"
    assert metrics.freshness_outcome == "verified_unchanged"


def test_job_record_to_schema_with_hash_decision_does_not_raise() -> None:
    """Store → Job mapping must not ValidationError on hash_decision (live 500 root)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/freshness-doc"],
        job_type="freshness_refresh",
    )
    updated = store.update_job(
        record.job_id,
        status="completed",
        metrics={
            "freshness_outcome": "verified_unchanged",
            "documents_processed": 1,
            "hash_decision": "skip_rechunk",
        },
    )
    assert updated is not None
    schema = job_record_to_schema(updated)
    assert schema.metrics is not None
    assert schema.metrics.hash_decision == "skip_rechunk"


def test_get_jobs_returns_200_when_store_has_hash_decision_metrics() -> None:
    """App boundary: GET /jobs must list freshness jobs with hash_decision (F32)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/freshness-doc"],
        job_type="freshness_refresh",
    )
    _ = store.update_job(
        record.job_id,
        status="completed",
        metrics={
            "freshness_outcome": "verified_unchanged",
            "documents_processed": 1,
            "hash_decision": "skip_rechunk",
        },
    )
    client = TestClient(create_app(store=store, require_proxy_auth=False))
    response = client.get("/jobs")
    assert response.status_code == HTTPStatus.OK, response.text
    body = response_json_object(response)
    jobs = json_list(body, "jobs")
    assert len(jobs) >= 1
    matched = find_json_object_by_str(jobs, "job_id", str(record.job_id))
    metrics = as_json_object(matched["metrics"])
    assert json_str(metrics, "hash_decision") == "skip_rechunk"


@pytest.mark.live
def test_live_modal_get_jobs_with_supabase_jwt_returns_200() -> None:
    """Live: proxy key + Supabase JWT → GET /jobs 200 (not 401/500)."""
    proxy = os.environ.get("VECINITA_MODAL_PROXY_KEY", "").strip()
    base = (os.environ.get("VECINITA_MODAL_DATA_MGMT_URL") or "").rstrip("/")
    supabase = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    email = os.environ.get("SUPABASE_ADMIN_EMAIL", "").strip()
    password = os.environ.get("SUPABASE_ADMIN_PASSWORD", "").strip()
    if not all([proxy, base, supabase, anon, email, password]):
        pytest.skip("Need Modal proxy URL/key + Supabase admin password grant env")

    token_resp = httpx.post(
        f"{supabase}/auth/v1/token?grant_type=password",
        headers={"apikey": anon, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30.0,
    )
    assert token_resp.status_code == HTTPStatus.OK, token_resp.text[:200]
    token_payload = cast("object", token_resp.json())
    token_body = as_json_object(token_payload)
    access_raw = token_body.get("access_token")
    assert isinstance(access_raw, str)
    assert access_raw
    access = access_raw

    response = httpx.get(
        f"{base}/jobs",
        headers={
            "X-Vecinita-Proxy-Key": proxy,
            "Authorization": f"Bearer {access}",
        },
        timeout=60.0,
    )
    assert response.status_code == HTTPStatus.OK, (
        f"Expected GET /jobs 200, got {response.status_code}: {response.text[:300]}"
    )
    body = response_json_object(response)
    assert isinstance(body.get("jobs"), list)

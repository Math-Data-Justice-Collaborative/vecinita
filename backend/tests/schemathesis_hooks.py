"""Schemathesis hooks for schema coverage reporting and live CLI stability."""

from __future__ import annotations

import os

try:
    import tracecov
except Exception:  # pragma: no cover - optional during partial installs
    tracecov = None

if tracecov is not None:
    tracecov.schemathesis.install()

from schemathesis import HookContext, hook

# Live gateway runs: override with real values that exist in the target DB / job store when available.
_DEFAULT_SOURCE_URL = "https://example.org/community-resource-guide"
_DEFAULT_SCRAPE_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
_DEFAULT_SCRAPE_TARGET_URL = "https://example.com/page"


def _source_url() -> str:
    return os.environ.get("SCHEMATHESIS_SOURCE_URL", _DEFAULT_SOURCE_URL).strip()


def _scrape_job_id() -> str:
    return os.environ.get("SCHEMATHESIS_SCRAPE_JOB_ID", _DEFAULT_SCRAPE_JOB_ID).strip()


def _scrape_post_url() -> str:
    return os.environ.get("SCHEMATHESIS_SCRAPE_URL", _DEFAULT_SCRAPE_TARGET_URL).strip()


@hook
def map_body(context: HookContext, body):  # noqa: ANN001
    """Normalize bodies that are easy for Schemathesis to over-generate vs FastAPI validation."""
    operation = context.operation
    if operation is None:
        return body
    path = operation.path
    method = operation.method.upper()
    if path == "/model-selection" and method == "POST":
        return {"provider": "ollama", "model": None, "lock": False}
    if path == "/api/v1/scrape" and method == "POST":
        return {
            "urls": [_scrape_post_url()],
            "force_loader": "auto",
            "stream": False,
        }
    return body


@hook
def map_query(context: HookContext, query):  # noqa: ANN001
    """Use a stable source_url for document preview/download so tests are deterministic."""
    operation = context.operation
    if operation is None:
        return query
    if operation.path not in {
        "/api/v1/documents/preview",
        "/api/v1/documents/download-url",
    }:
        return query
    out = dict(query)
    out["source_url"] = _source_url()
    return out


@hook
def map_path_parameters(context: HookContext, path_parameters):  # noqa: ANN001
    """Use a well-formed job id for scrape status/cancel (set env to a real job when testing live)."""
    operation = context.operation
    if operation is None:
        return path_parameters
    if operation.path not in {"/api/v1/scrape/{job_id}", "/api/v1/scrape/{job_id}/cancel"}:
        return path_parameters
    out = dict(path_parameters)
    out["job_id"] = _scrape_job_id()
    return out

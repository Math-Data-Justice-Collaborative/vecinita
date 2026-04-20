"""Schemathesis hooks for schema coverage reporting and live CLI stability.

Schema-level coverage (TraceCov) tracks operations, parameters, JSON Schema
keywords, examples, and response codes—not only whether an endpoint was hit.
See https://schemathesis.readthedocs.io/en/stable/guides/coverage/

Lifecycle hooks follow the Schemathesis hooks reference (schema load + request flow):
https://schemathesis.readthedocs.io/en/stable/reference/hooks/

For **pytest** schema coverage, TraceCov also needs a session ``tracecov_schema`` fixture
(see ``tests/integration/conftest.py``); ``tracecov.schemathesis.install()`` here is mainly for **``schemathesis run``** CLI.

TraceCov registers CLI report options (e.g. ``SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH``,
``SCHEMATHESIS_COVERAGE_FORMAT``). Set ``SCHEMATHESIS_COVERAGE_FAIL_UNDER`` (0–100) to fail
``schemathesis run`` when schema coverage is below that percentage on any TraceCov dimension.
Set ``SCHEMATHESIS_COVERAGE`` to ``false`` to skip ``tracecov.schemathesis.install()`` (matches the guide / Docker opt-out pattern).
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _patch_tracecov_cli_coverage_threshold() -> None:
    """Fail ``schemathesis run`` when TraceCov schema coverage is below a minimum.

    TraceCov exposes ``--tracecov-fail-under`` for pytest only; the Schemathesis CLI handler
    does not read ``schemathesis.toml`` for thresholds (the project file schema forbids extra keys).
    Use env ``SCHEMATHESIS_COVERAGE_FAIL_UNDER`` (0–100) for the same gate on CLI runs.
    """
    raw = os.environ.get("SCHEMATHESIS_COVERAGE_FAIL_UNDER", "").strip()
    if not raw:
        return
    try:
        minimum = int(raw)
    except ValueError:
        logger.warning("Ignoring invalid SCHEMATHESIS_COVERAGE_FAIL_UNDER=%r", raw)
        return
    if not 0 <= minimum <= 100:
        logger.warning("Ignoring SCHEMATHESIS_COVERAGE_FAIL_UNDER out of range [0, 100]: %s", raw)
        return

    try:
        from schemathesis.cli.commands.run import executor as _st_executor
    except Exception:  # pragma: no cover - optional during partial installs
        return

    handler_cls = next(
        (
            h
            for h in _st_executor.CUSTOM_HANDLERS
            if getattr(h, "__name__", "") == "TracecovHandler"
            and getattr(h, "__module__", "") == "tracecov.schemathesis.handler"
        ),
        None,
    )
    if handler_cls is None:
        logger.warning(
            "TracecovHandler not found on Schemathesis CUSTOM_HANDLERS; "
            "skipping SCHEMATHESIS_COVERAGE_FAIL_UNDER patch"
        )
        return

    import click
    from schemathesis.engine import events as _engine_events

    _orig_handle_event = handler_cls.handle_event

    def _handle_event_with_threshold(self: Any, ctx: Any, event: object) -> None:
        _orig_handle_event(self, ctx, event)
        if isinstance(event, _engine_events.EngineFinished) and self.coverage_map is not None:
            vmin = float(minimum)
            violations = self.coverage_map.check_thresholds(
                operations=vmin,
                parameters=vmin,
                keywords=vmin,
                examples=vmin,
                responses=vmin,
            )
            if violations:
                ctx.exit_code = 1
                ctx.add_summary_line("")
                ctx.add_summary_line(
                    click.style("Schema coverage below required threshold", bold=True, fg="red")
                )
                for v in violations:
                    ctx.add_summary_line(
                        f"  {v['dimension']}: {v['actual']:.1f}% (required {v['minimum']:.0f}%)"
                    )

    handler_cls.handle_event = _handle_event_with_threshold  # type: ignore[method-assign]


tracecov = None
_cov = os.environ.get("SCHEMATHESIS_COVERAGE", "").strip().lower()
if _cov not in ("0", "false", "no"):
    try:
        import tracecov as _tracecov_mod

        tracecov = _tracecov_mod
    except Exception:  # pragma: no cover - optional during partial installs
        tracecov = None
    if tracecov is not None:
        tracecov.schemathesis.install()
        _patch_tracecov_cli_coverage_threshold()

from schemathesis import HookContext, hook  # noqa: E402

# Live gateway runs: override with real values that exist in the target DB / job store when available.
_DEFAULT_SOURCE_URL = "https://example.org/community-resource-guide"
_DEFAULT_SCRAPE_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
_DEFAULT_SCRAPE_TARGET_URL = "https://example.com/page"
# Tracked Modal registry ids (live runs: set to a real id to avoid repeated 404 warnings).
_DEFAULT_MODAL_REGISTRY_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
_DEFAULT_STREAM_QUESTION = "What is Vecinita?"
_DEFAULT_ASK_QUESTION = "What is Vecinita?"
# Data Management (scraper) API — https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json
_DEFAULT_DM_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
_DM_SUBMIT_URL = "https://example.org/page"


def _source_url() -> str:
    return os.environ.get("SCHEMATHESIS_SOURCE_URL", _DEFAULT_SOURCE_URL).strip()


def _documents_path_source_url(path: str) -> str:
    """``source_url`` for preview vs download when the DB has distinct rows per route."""
    p = (path or "").strip()
    if p == "/api/v1/documents/preview":
        override = os.environ.get("SCHEMATHESIS_DOCUMENTS_PREVIEW_SOURCE_URL", "").strip()
        if override:
            return override
    if p == "/api/v1/documents/download-url":
        override = os.environ.get("SCHEMATHESIS_DOCUMENTS_DOWNLOAD_SOURCE_URL", "").strip()
        if override:
            return override
    return _source_url()


def _scrape_job_id() -> str:
    return os.environ.get("SCHEMATHESIS_SCRAPE_JOB_ID", _DEFAULT_SCRAPE_JOB_ID).strip()


def _modal_scraper_job_id() -> str:
    """Path param for ``/api/v1/modal-jobs/scraper/{job_id}`` (optional override)."""
    return os.environ.get("SCHEMATHESIS_MODAL_SCRAPER_JOB_ID", _scrape_job_id()).strip()


def _scrape_post_url() -> str:
    return os.environ.get("SCHEMATHESIS_SCRAPE_URL", _DEFAULT_SCRAPE_TARGET_URL).strip()


def _modal_registry_gateway_job_id() -> str:
    return os.environ.get(
        "SCHEMATHESIS_MODAL_GATEWAY_JOB_ID", _DEFAULT_MODAL_REGISTRY_JOB_ID
    ).strip()


def _stream_question() -> str:
    return os.environ.get("SCHEMATHESIS_STREAM_QUESTION", _DEFAULT_STREAM_QUESTION).strip()


def _ask_question() -> str:
    return os.environ.get("SCHEMATHESIS_ASK_QUESTION", _DEFAULT_ASK_QUESTION).strip()


def _data_management_job_id() -> str:
    return os.environ.get("SCHEMATHESIS_DM_JOB_ID", _DEFAULT_DM_JOB_ID).strip()


def _data_management_bearer() -> str | None:
    t = os.environ.get("SCRAPER_SCHEMATHESIS_BEARER", "").strip()
    if t:
        return t
    raw = os.environ.get("SCRAPER_API_KEYS", "").strip()
    if not raw:
        return None
    return raw.split(",")[0].strip() or None


def _hooks_verbose() -> bool:
    return os.environ.get("SCHEMATHESIS_HOOKS_VERBOSE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@hook
def before_load_schema(context: HookContext, raw_schema: dict[str, Any]) -> None:
    """Spin-up: invoked once per raw OpenAPI document before it is parsed (GLOBAL).

    Use for logging, optional ``raw_schema`` normalization, or other one-shot setup
    tied to schema load. See :func:`after_load_schema` for the matching post-parse hook.
    """
    _ = context
    if not _hooks_verbose():
        return
    info = raw_schema.get("info")
    if not isinstance(info, dict):
        info = {}
    logger.info(
        "schemathesis hooks: before_load_schema title=%r version=%r spec=%r",
        info.get("title"),
        info.get("version"),
        raw_schema.get("openapi") or raw_schema.get("swagger"),
    )


@hook
def after_load_schema(context: HookContext, schema: Any) -> None:  # noqa: ANN401
    """Spin-up (post-parse): invoked once after the schema object exists (GLOBAL).

    Suite-level teardown belongs in pytest fixtures or the test runner; this hook
    records load metadata only. Per-request cleanup can use :func:`after_call` /
    :func:`after_validate`.
    """
    _ = context
    if not _hooks_verbose():
        return
    raw = getattr(schema, "raw_schema", None) or {}
    info = raw.get("info") if isinstance(raw, dict) else {}
    if not isinstance(info, dict):
        info = {}
    loc = getattr(schema, "location", None)
    try:
        stat = schema.statistic
        total = stat.operations.total
        selected = stat.operations.selected
    except Exception:  # pragma: no cover - defensive
        total = selected = -1
    logger.info(
        "schemathesis hooks: after_load_schema location=%r title=%r operations=%s/%s",
        loc,
        info.get("title"),
        selected,
        total,
    )


@hook
def after_call(context: HookContext, case: Any, response: Any) -> None:  # noqa: ANN001,ANN401
    """Tear-down hook after each HTTP response (GLOBAL / SCHEMA).

    Reserved for response post-processing or releasing per-request resources allocated
    in :func:`before_call`. Mutate ``response`` in place only when required.
    """
    _ = context, case, response


@hook
def after_validate(  # noqa: ANN001
    context: HookContext,
    case: Any,
    response: Any,
    results: list[Any],
) -> None:
    """Tear-down / observation after all checks run on a response (all scopes).

    Use for metrics, cassette writers, or failure logging. Keep work cheap: this
    runs for every validated case in examples, coverage, fuzzing, and stateful phases.
    """
    _ = context, case, response
    if not _hooks_verbose() or not results:
        return
    try:
        from schemathesis.checks import CheckResult
        from schemathesis.engine import Status
    except Exception:  # pragma: no cover
        return
    for r in results:
        if not isinstance(r, CheckResult):
            continue
        if r.status is Status.FAILURE and r.failure is not None:
            logger.warning("schemathesis check failure: %s — %s", r.name, r.failure)


@hook
def map_body(context: HookContext, body):  # noqa: ANN001
    """Normalize bodies that are easy for Schemathesis to over-generate vs FastAPI validation."""
    operation = context.operation
    if operation is None:
        return body
    if body is None:
        body = {}
    path = operation.path
    method = operation.method.upper()
    if path == "/model-selection" and method == "POST":
        return {"provider": "ollama", "model": None, "lock": False}
    if path == "/jobs" and method == "POST":
        return {
            "url": os.environ.get("SCHEMATHESIS_DM_SUBMIT_URL", _DM_SUBMIT_URL).strip(),
            "user_id": os.environ.get("SCHEMATHESIS_DM_USER_ID", "schemathesis").strip(),
        }
    if path == "/api/v1/scrape" and method == "POST":
        return {
            "urls": [_scrape_post_url()],
            "force_loader": "auto",
            "stream": False,
        }
    if path == "/api/v1/modal-jobs/scraper" and method == "POST":
        from src.utils.postgres_json_sanitize import sanitize_postgres_json_payload

        out = dict(body) if isinstance(body, dict) else {}
        for key in ("crawl_config", "chunking_config", "metadata"):
            if key in out and out[key] is not None:
                out[key] = sanitize_postgres_json_payload(out[key])
        return out
    return body


@hook
def map_query(context: HookContext, query):  # noqa: ANN001
    """Use a stable source_url for document preview/download so tests are deterministic."""
    operation = context.operation
    if operation is None:
        return query
    if operation.path == "/jobs" and operation.method.upper() == "GET":
        return {"limit": 10}
    if operation.path == "/api/v1/modal-jobs/scraper" and operation.method.upper() == "GET":
        out = {} if query is None else dict(query)
        uid = out.get("user_id")
        if uid is None or str(uid).strip().lower() in ("", "null", "none"):
            out.pop("user_id", None)
        return out
    if operation.path == "/api/v1/ask/stream" and operation.method.upper() == "GET":
        out = {} if query is None else dict(query)
        out["question"] = _stream_question()
        return out
    if operation.path == "/api/v1/ask" and operation.method.upper() == "GET":
        # Stable query bundle: avoids Schemathesis rejecting invalid tag_match_mode / rerank_top_k, etc.
        return {
            "question": _ask_question(),
            "tag_match_mode": "any",
            "include_untagged_fallback": True,
            "rerank": False,
            "rerank_top_k": 10,
        }
    if operation.path == "/api/v1/documents/overview" and operation.method.upper() == "GET":
        return {"tags": None, "tag_match_mode": "any", "include_test_data": False}
    if operation.path not in {
        "/api/v1/documents/preview",
        "/api/v1/documents/download-url",
    }:
        return query
    out = {} if query is None else dict(query)
    out["source_url"] = _documents_path_source_url(operation.path or "")
    if operation.path == "/api/v1/documents/preview":
        out["limit"] = 3
    return out


@hook
def map_path_parameters(context: HookContext, path_parameters):  # noqa: ANN001
    """Use a well-formed job id for scrape status/cancel (set env to a real job when testing live)."""
    operation = context.operation
    if operation is None:
        return path_parameters
    if operation.path in {"/jobs/{job_id}", "/jobs/{job_id}/cancel"}:
        out = {} if path_parameters is None else dict(path_parameters)
        out["job_id"] = _data_management_job_id()
        return out
    if operation.path not in {
        "/api/v1/scrape/{job_id}",
        "/api/v1/scrape/{job_id}/cancel",
        "/api/v1/modal-jobs/scraper/{job_id}",
        "/api/v1/modal-jobs/scraper/{job_id}/cancel",
        "/api/v1/modal-jobs/registry/{gateway_job_id}",
    }:
        return path_parameters
    out = {} if path_parameters is None else dict(path_parameters)
    path = operation.path or ""
    if "gateway_job_id" in path:
        out["gateway_job_id"] = _modal_registry_gateway_job_id()
    elif "/modal-jobs/scraper/" in path:
        out["job_id"] = _modal_scraper_job_id()
    else:
        out["job_id"] = _scrape_job_id()
    return out


@hook
def before_call(context: HookContext, case, kwargs: dict[str, Any]) -> None:  # noqa: ANN001
    """Strip Schemathesis probe query keys; attach scraper Bearer for Data Management ``/jobs`` routes."""
    op = context.operation
    if op is not None and (op.path or "").startswith("/jobs"):
        token = _data_management_bearer()
        if token:
            hdrs = getattr(case, "headers", None)
            if hdrs is None:
                case.headers = {}
                hdrs = case.headers
            if isinstance(hdrs, dict):
                hdrs.setdefault("Authorization", f"Bearer {token}")
            kh = kwargs.get("headers")
            if isinstance(kh, dict):
                kh.setdefault("Authorization", f"Bearer {token}")

    q = getattr(case, "query", None)
    if not isinstance(q, dict):
        return
    for key in list(q.keys()):
        if str(key).lower().startswith("x-schemathesis"):
            q.pop(key, None)

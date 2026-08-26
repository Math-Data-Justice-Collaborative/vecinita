"""Aggregate dependency health checks for admin dashboard."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
from sqlalchemy import text
from vecinita_shared_schemas.internal_write import HealthAggregateResponse, ServiceHealth

from vecinita_internal_write_api.deps import dependency_health_url

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def aggregate_health(*, engine: Engine) -> HealthAggregateResponse:
    """Probe database and configured upstream services."""
    timeout_ms = int(os.environ.get("VECINITA_HEALTH_TIMEOUT_MS", "3000"))
    timeout_s = timeout_ms / 1000.0

    service_urls: dict[str, str | None] = {
        "chat_rag_backend": os.environ.get("VECINITA_CHAT_RAG_URL"),
        "modal_data_management": os.environ.get("VECINITA_MODAL_DATA_MGMT_URL"),
        "modal_embedding": os.environ.get("VECINITA_MODAL_EMBED_URL"),
        "modal_llm": os.environ.get("VECINITA_MODAL_LLM_URL"),
        "chat_rag_frontend": os.environ.get("VECINITA_CHAT_FRONTEND_URL"),
        "admin_frontend": os.environ.get("VECINITA_ADMIN_FRONTEND_URL"),
    }

    results: dict[str, ServiceHealth] = {}

    db_start = time.monotonic()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ms = int((time.monotonic() - db_start) * 1000)
        results["database"] = ServiceHealth(status="up", latency_ms=db_ms)
    except Exception as exc:  # noqa: BLE001  # aggregate health must tolerate any dependency failure
        results["database"] = ServiceHealth(status="down", error=str(exc))

    results["internal_write_api"] = ServiceHealth(status="up", latency_ms=0)

    for svc_name, url in service_urls.items():
        if not url:
            results[svc_name] = ServiceHealth(status="down", error="not configured")
            continue
        start = time.monotonic()
        try:
            health_url = dependency_health_url(url)
            resp = httpx.get(health_url, timeout=timeout_s)
            ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == HTTPStatus.OK:
                results[svc_name] = ServiceHealth(status="up", latency_ms=ms)
            else:
                results[svc_name] = ServiceHealth(status="down", error=f"HTTP {resp.status_code}")
        except Exception as exc:  # noqa: BLE001  # aggregate health must tolerate any dependency failure
            results[svc_name] = ServiceHealth(status="down", error=str(exc))

    all_up = all(s.status == "up" for s in results.values())
    return HealthAggregateResponse(
        status="healthy" if all_up else "degraded",
        services=results,
        checked_at=datetime.now(UTC),
    )

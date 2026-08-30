"""Direct unit coverage for F84 metrics_query helpers (branch gate)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from vecinita_internal_write_api import metrics_query
from vecinita_internal_write_api.metrics_query import (
    fetch_metrics_summary,
    fetch_metrics_timeseries,
    parse_metrics_metric,
    parse_metrics_window,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@pytest.mark.parametrize("window", ["1h", "24h", "7d", "30d"])
def test_parse_metrics_window_accepts(window: str) -> None:
    """All documented windows parse."""
    assert parse_metrics_window(window) == window


def test_parse_metrics_window_rejects() -> None:
    """Unknown window → 422."""
    with pytest.raises(HTTPException) as exc:
        _ = parse_metrics_window("year")
    assert exc.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "metric",
    [
        "ingest_success_rate",
        "chat_success_rate",
        "embed_success_rate",
        "ingest_volume",
        "chat_volume",
        "embed_volume",
    ],
)
def test_parse_metrics_metric_accepts(metric: str) -> None:
    """All documented metrics parse."""
    assert parse_metrics_metric(metric) == metric


def test_parse_metrics_metric_rejects() -> None:
    """Unknown metric → 422."""
    with pytest.raises(HTTPException) as exc:
        _ = parse_metrics_metric("latency_p99")
    assert exc.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("window", ["1h", "24h", "7d", "30d"])
def test_fetch_metrics_summary_all_windows(engine: Engine, window: str) -> None:
    """Summary succeeds for every window."""
    body = fetch_metrics_summary(engine=engine, window=parse_metrics_window(window))
    assert body.window == window
    assert set(body.workloads) == {"ingest", "chat", "embed"}
    assert body.workloads["embed"].no_context is None
    assert 0.0 <= body.workloads["chat"].success_rate <= 1.0


@pytest.mark.parametrize(
    ("metric", "window"),
    [
        ("ingest_success_rate", "1h"),
        ("ingest_volume", "24h"),
        ("chat_success_rate", "7d"),
        ("chat_volume", "30d"),
        ("embed_success_rate", "1h"),
        ("embed_volume", "24h"),
    ],
)
def test_fetch_metrics_timeseries_matrix(
    engine: Engine,
    metric: str,
    window: str,
) -> None:
    """Timeseries covers ingest/chat/embed x window truncations."""
    body = fetch_metrics_timeseries(
        engine=engine,
        metric=parse_metrics_metric(metric),
        window=parse_metrics_window(window),
    )
    assert body.metric == metric
    assert body.window == window
    assert isinstance(body.buckets, list)


def test_summary_omits_latency_when_window_has_no_rows(engine: Engine) -> None:
    """Summary with a future window start leaves latency_ms empty."""
    future = datetime.now(tz=UTC) + timedelta(days=30)
    with patch.object(metrics_query, "_window_start", return_value=future):
        body = fetch_metrics_summary(engine=engine, window="1h")
    assert body.latency_ms == {}

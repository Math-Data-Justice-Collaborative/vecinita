"""Experiment result IO and aggregation for golden-set sweeps (F36)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from vecinita_shared_schemas.json_types import JsonObject, as_json_object

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_DEFAULT_GROUP_BY: tuple[str, ...] = (
    "model_id",
    "temperature",
    "top_k",
    "prompt_name",
)
_DEFAULT_METRICS: tuple[str, ...] = (
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
    "wall_time_s",
    "latency_p95_ms",
    "spawn_wall_time_s",
)


def new_experiment_id(*, slug: str = "sweep") -> str:
    """Return a filesystem-safe experiment id with UTC timestamp."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slug.strip()) or "sweep"
    return f"{stamp}_{safe}_{uuid4().hex[:8]}"


def experiment_path(results_dir: Path, experiment_id: str) -> Path:
    """Path for one experiment JSON file."""
    return results_dir / f"{experiment_id}.json"


def write_experiment(
    *,
    results_dir: Path,
    experiment_id: str,
    payload: JsonObject,
) -> Path:
    """Write one experiment JSON under ``results_dir``; return the path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = experiment_path(results_dir, experiment_id)
    body = {
        "experiment_id": experiment_id,
        "written_at": datetime.now(UTC).isoformat(),
        **payload,
    }
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_experiment(path: Path) -> JsonObject:
    """Load and validate one experiment JSON object."""
    loaded = as_json_object(cast("object", json.loads(path.read_text(encoding="utf-8"))))
    if "cells" not in loaded:
        msg = f"experiment missing cells: {path}"
        raise ValueError(msg)
    return loaded


def list_experiment_paths(results_dir: Path) -> list[Path]:
    """List ``*.json`` experiment files in ``results_dir`` (non-recursive)."""
    if not results_dir.is_dir():
        return []
    return sorted(path for path in results_dir.glob("*.json") if path.is_file())


def load_experiments(results_dir: Path) -> list[JsonObject]:
    """Load all experiment JSONs from a results folder."""
    return [load_experiment(path) for path in list_experiment_paths(results_dir)]


def _cell_config(cell: JsonObject) -> JsonObject:
    config = cell.get("config")
    if isinstance(config, dict):
        return as_json_object(cast("object", config))
    return {}


def _cell_averages(cell: JsonObject) -> JsonObject:
    averages = cell.get("averages")
    if isinstance(averages, dict):
        return as_json_object(cast("object", averages))
    return {}


def _group_key(cell: JsonObject, *, group_by: Sequence[str]) -> tuple[str, ...]:
    config = _cell_config(cell)
    parts: list[str] = []
    for field in group_by:
        if field == "prompt_name":
            value = config.get("prompt_name", cell.get("prompt_name", "default"))
        elif field in config:
            value = config.get(field)
        elif field in cell:
            value = cell.get(field)
        else:
            value = None
        parts.append("null" if value is None else str(value))
    return tuple(parts)


def _metric_value(cell: JsonObject, metric: str) -> float | None:
    averages = _cell_averages(cell)
    raw: object | None
    if metric == "spawn_wall_time_s":
        raw = cell.get("spawn_wall_time_s")
    elif metric in averages:
        raw = averages.get(metric)
    else:
        custom_raw = averages.get("custom_scores")
        if isinstance(custom_raw, dict):
            custom = as_json_object(cast("object", custom_raw))
            raw = custom.get(metric)
        else:
            return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int | float):
        return float(raw)
    return None


def aggregate_experiments(
    experiments: Sequence[JsonObject],
    *,
    group_by: Sequence[str] | None = None,
    metrics: Sequence[str] | None = None,
) -> JsonObject:
    """Aggregate cell averages across experiments, grouped by config fields.

    Parameters
    ----------
    experiments
        Loaded experiment payloads (each with a ``cells`` array).
    group_by
        Config/cell fields used as the grouping key.
    metrics
        Numeric fields to average (from cell averages, spawn time, or custom scores).

    Returns:
    -------
    JsonObject
        ``groups`` list with key fields, sample counts, and mean metrics.
    """
    resolved_group_by = tuple(group_by) if group_by else _DEFAULT_GROUP_BY
    resolved_metrics = tuple(metrics) if metrics else _DEFAULT_METRICS

    buckets: dict[tuple[str, ...], dict[str, list[float]]] = {}
    bucket_meta: dict[tuple[str, ...], JsonObject] = {}
    experiment_ids: list[str] = []

    for experiment in experiments:
        exp_id = experiment.get("experiment_id")
        if isinstance(exp_id, str):
            experiment_ids.append(exp_id)
        cells_raw = experiment.get("cells")
        if not isinstance(cells_raw, list):
            continue
        for cell_raw in cast("list[object]", cells_raw):
            cell = as_json_object(cell_raw)
            key = _group_key(cell, group_by=resolved_group_by)
            if key not in buckets:
                buckets[key] = {metric: [] for metric in resolved_metrics}
                config = _cell_config(cell)
                bucket_meta[key] = {
                    field: (
                        config.get("prompt_name", cell.get("prompt_name", "default"))
                        if field == "prompt_name"
                        else config.get(field, cell.get(field))
                    )
                    for field in resolved_group_by
                }
            for metric in resolved_metrics:
                value = _metric_value(cell, metric)
                if value is not None:
                    buckets[key][metric].append(value)

    groups: list[JsonObject] = []
    for key in sorted(buckets):
        means: JsonObject = {}
        counts: JsonObject = {}
        for metric, values in buckets[key].items():
            counts[metric] = len(values)
            means[metric] = (sum(values) / len(values)) if values else None
        groups.append(
            {
                "key": dict(zip(resolved_group_by, key, strict=True)),
                "fields": bucket_meta[key],
                "n_cells": max((cast("int", counts[m]) for m in counts), default=0),
                "means": means,
                "counts": counts,
            }
        )

    return {
        "experiment_count": len(experiments),
        "experiment_ids": experiment_ids,
        "group_by": list(resolved_group_by),
        "metrics": list(resolved_metrics),
        "groups": groups,
    }

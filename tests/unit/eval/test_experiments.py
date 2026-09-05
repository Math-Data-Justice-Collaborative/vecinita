"""Unit tests for experiment IO and aggregation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from vecinita_eval.experiments import (
    aggregate_experiments,
    load_experiments,
    write_experiment,
)
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit


def _sample_cell(  # noqa: PLR0913
    *,
    model_id: str,
    temperature: float,
    prompt_name: str,
    retrieval: float,
    faith: float,
    wall: float,
) -> JsonObject:
    return {
        "label": f"{model_id}|p={prompt_name}|t={temperature}",
        "prompt_name": prompt_name,
        "spawn_wall_time_s": 30.0,
        "config": {
            "model_id": model_id,
            "model_type": "Qwen/Qwen2.5-1.5B-Instruct",
            "prompt_name": prompt_name,
            "temperature": temperature,
            "top_k": 5,
            "system_prompt": "Answer from context.",
            "rules": [],
        },
        "averages": {
            "run_count": 2,
            "wall_time_s": wall,
            "retrieval_relevance": retrieval,
            "faithfulness": faith,
            "answer_relevancy": 0.8,
            "latency_p95_ms": 120.0,
            "custom_scores": {},
        },
        "runs": [],
        "rows": [],
    }


def test_write_and_load_experiments_round_trip(tmp_path: Path) -> None:
    """Experiments are written as JSON files and reloaded from a folder."""
    payload: JsonObject = {
        "runs_per_config": 2,
        "row_count": 1,
        "system_prompt": "hi",
        "rules": [],
        "cells": [
            _sample_cell(
                model_id="qwen2.5:1.5b-instruct",
                temperature=0.2,
                prompt_name="concise",
                retrieval=1.0,
                faith=0.9,
                wall=10.0,
            )
        ],
    }
    path = write_experiment(
        results_dir=tmp_path,
        experiment_id="demo_exp",
        payload=payload,
    )
    assert path.name == "demo_exp.json"
    loaded = load_experiments(tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["experiment_id"] == "demo_exp"
    cells = loaded[0]["cells"]
    assert isinstance(cells, list)
    assert len(cast("list[object]", cells)) == 1


def test_aggregate_experiments_groups_by_model_and_prompt(tmp_path: Path) -> None:
    """Aggregation means metrics across experiments for matching group keys."""
    _ = write_experiment(
        results_dir=tmp_path,
        experiment_id="exp_a",
        payload={
            "cells": [
                _sample_cell(
                    model_id="qwen2.5:1.5b-instruct",
                    temperature=0.2,
                    prompt_name="concise",
                    retrieval=0.8,
                    faith=0.6,
                    wall=10.0,
                ),
                _sample_cell(
                    model_id="qwen3:8b",
                    temperature=0.2,
                    prompt_name="concise",
                    retrieval=1.0,
                    faith=0.9,
                    wall=20.0,
                ),
            ]
        },
    )
    _ = write_experiment(
        results_dir=tmp_path,
        experiment_id="exp_b",
        payload={
            "cells": [
                _sample_cell(
                    model_id="qwen2.5:1.5b-instruct",
                    temperature=0.2,
                    prompt_name="concise",
                    retrieval=1.0,
                    faith=0.8,
                    wall=14.0,
                )
            ]
        },
    )
    aggregate = aggregate_experiments(
        load_experiments(tmp_path),
        group_by=["model_id", "prompt_name"],
        metrics=["retrieval_relevance", "faithfulness", "wall_time_s"],
    )
    expected_experiment_count = 2
    expected_groups = 2
    assert aggregate["experiment_count"] == expected_experiment_count
    groups = aggregate["groups"]
    assert isinstance(groups, list)
    group_list = cast("list[object]", groups)
    assert len(group_list) == expected_groups
    by_model: dict[str, JsonObject] = {}
    for group_raw in group_list:
        group = as_json_object(group_raw)
        fields = as_json_object(group["fields"])
        model_id = fields["model_id"]
        assert isinstance(model_id, str)
        by_model[model_id] = group
    small = by_model["qwen2.5:1.5b-instruct"]
    means = as_json_object(small["means"])
    expected_retrieval = 0.9
    expected_faith = 0.7
    expected_wall = 12.0
    assert means["retrieval_relevance"] == expected_retrieval
    assert means["faithfulness"] == expected_faith
    assert means["wall_time_s"] == expected_wall

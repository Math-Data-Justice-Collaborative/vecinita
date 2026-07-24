"""Unit tests for golden-set model/parameter sweep helpers."""

from __future__ import annotations

from typing import cast

import pytest
from vecinita_eval.criteria import EvalCriterionDef
from vecinita_eval.golden import GoldenRow
from vecinita_eval.runner import RowMetrics, RowResult
from vecinita_eval.sweep import (
    PromptVariant,
    SweepCell,
    SweepRunRecord,
    average_run_records,
    build_config_grid,
    config_snapshot,
    filter_golden_rows,
    parse_csv_floats,
    parse_csv_ints,
    parse_csv_strs,
    resolve_model_type,
    summarize_cell,
)
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID, EvalConfig
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.unit


def test_parse_csv_strs_splits_and_strips() -> None:
    """CSV string parsing trims tokens and drops empties."""
    assert parse_csv_strs("a, b ,c") == ["a", "b", "c"]
    assert parse_csv_strs("") == []
    assert parse_csv_strs("  qwen3:8b  ") == ["qwen3:8b"]


def test_parse_csv_floats_and_ints() -> None:
    """CSV float/int helpers parse numeric lists."""
    assert parse_csv_floats("0,0.2, 0.5") == [0.0, 0.2, 0.5]
    assert parse_csv_ints("3,5, 10") == [3, 5, 10]


def test_build_config_grid_cartesian_product() -> None:
    """Grid is the product of prompts x models x temperatures x top_k values."""
    cells = build_config_grid(
        models=["qwen2.5:1.5b-instruct", "qwen3:8b"],
        temperatures=[0.0, 0.2],
        top_ks=[3, 5],
        max_tokens_list=[128],
        min_retrieval_scores=[0.2],
        judge_temperatures=[0.2],
        prompts=[PromptVariant(name="default", text="Answer from context.")],
        base=EvalConfig(),
    )
    expected_cells = 8
    assert len(cells) == expected_cells
    labels = {cell.label for cell in cells}
    assert "qwen3:8b|p=default|t=0.2|k=5|mt=128|mrs=0.2|jt=0.2" in labels
    assert all(isinstance(cell.config, EvalConfig) for cell in cells)


def test_build_config_grid_defaults_to_base_model_when_models_empty() -> None:
    """Empty models list falls back to EvalConfig.model_id."""
    cells = build_config_grid(
        models=[],
        temperatures=[0.2],
        top_ks=[5],
        max_tokens_list=[256],
        min_retrieval_scores=[0.2],
        judge_temperatures=[0.2],
        prompts=[PromptVariant(name="default", text="Answer from context.")],
        base=EvalConfig(),
    )
    assert len(cells) == 1
    assert cells[0].config.model_id == DEFAULT_EVAL_MODEL_ID


def test_build_config_grid_includes_multiple_prompts() -> None:
    """Multiple prompt variants multiply the grid and set prompt_name."""
    cells = build_config_grid(
        models=["qwen3:8b"],
        temperatures=[0.2],
        top_ks=[5],
        max_tokens_list=[64],
        min_retrieval_scores=[0.2],
        judge_temperatures=[0.2],
        prompts=[
            PromptVariant(name="concise", text="Be concise."),
            PromptVariant(name="detailed", text="Be detailed."),
        ],
        base=EvalConfig(),
    )
    expected_cells = 2
    assert len(cells) == expected_cells
    assert {cell.prompt_name for cell in cells} == {"concise", "detailed"}
    assert cells[0].config.system_prompt == "Be concise."
    assert cells[1].config.system_prompt == "Be detailed."


def test_filter_golden_rows_by_id_domain_locale_and_limit() -> None:
    """Row filters honor id, domain, locale, and limit caps."""
    rows = [
        GoldenRow(
            id="community-food-pantry",
            locale="en",
            domain="community",
            question="q1",
            retrieval_expectation="hit",
            required_facts=("f",),
        ),
        GoldenRow(
            id="community-food-pantry",
            locale="es",
            domain="community",
            question="q2",
            retrieval_expectation="hit",
            required_facts=("f",),
        ),
        GoldenRow(
            id="housing-eviction-notice",
            locale="en",
            domain="housing",
            question="q3",
            retrieval_expectation="hit",
            required_facts=("f",),
        ),
    ]
    filtered = filter_golden_rows(
        rows,
        ids={"community-food-pantry"},
        domains=None,
        locales={"en"},
        limit=10,
    )
    assert len(filtered) == 1
    assert filtered[0].locale == "en"

    limited = filter_golden_rows(rows, ids=None, domains={"housing"}, locales=None, limit=1)
    assert len(limited) == 1
    assert limited[0].id == "housing-eviction-notice"


def test_resolve_model_type_maps_playground_tag_to_hf_repo() -> None:
    """Model type is the HuggingFace repo id for known playground tags."""
    assert resolve_model_type("qwen2.5:1.5b-instruct") == "Qwen/Qwen2.5-1.5B-Instruct"
    assert resolve_model_type("qwen3:8b") == "Qwen/Qwen3-8B-AWQ"
    assert resolve_model_type("not-a-real:model") == "unknown"


def test_config_snapshot_includes_params_prompt_rules_and_model_type() -> None:
    """Snapshot returns model params, type, system prompt, and rubric rules."""
    temperature = 0.1
    top_k = 3
    max_tokens = 128
    min_retrieval_score = 0.3
    config = EvalConfig(
        model_id="qwen3:8b",
        temperature=temperature,
        top_k=top_k,
        max_tokens=max_tokens,
        min_retrieval_score=min_retrieval_score,
        judge_temperature=0.0,
        system_prompt="Answer only from context. Do not invent phone numbers.",
        corpus_profile="staging",
    )
    criteria = [
        EvalCriterionDef(slug="no-pii", rubric="Must not invent personal phone numbers."),
    ]
    snap = config_snapshot(config, criteria=criteria)
    assert snap["model_id"] == "qwen3:8b"
    assert snap["model_type"] == "Qwen/Qwen3-8B-AWQ"
    assert snap["temperature"] == temperature
    assert snap["top_k"] == top_k
    assert snap["max_tokens"] == max_tokens
    assert snap["min_retrieval_score"] == min_retrieval_score
    assert snap["judge_temperature"] == 0.0
    assert snap["corpus_profile"] == "staging"
    assert snap["system_prompt"] == config.system_prompt
    rules_raw = snap["rules"]
    assert isinstance(rules_raw, list)
    assert len(cast("list[object]", rules_raw)) == 1
    first_rule = as_json_object(cast("object", rules_raw[0]))
    assert first_rule["slug"] == "no-pii"
    assert "phone" in str(first_rule["rubric"])


def test_average_run_records_means_scores_and_wall_times() -> None:
    """Multi-run averages mean scores, latency, and wall time."""
    runs = [
        SweepRunRecord(
            run_index=1,
            wall_time_s=10.0,
            retrieval_relevance=0.8,
            faithfulness=0.6,
            answer_relevancy=0.4,
            latency_p95_ms=100,
            custom_scores={"no-pii": 1.0},
        ),
        SweepRunRecord(
            run_index=2,
            wall_time_s=14.0,
            retrieval_relevance=1.0,
            faithfulness=0.8,
            answer_relevancy=None,
            latency_p95_ms=200,
            custom_scores={"no-pii": 0.5},
        ),
    ]
    expected_run_count = 2
    expected_wall = 12.0
    expected_retrieval = 0.9
    expected_faith = 0.7
    expected_relevancy = 0.4
    expected_p95 = 150.0
    expected_custom = 0.75
    avg = average_run_records(runs)
    assert avg["run_count"] == expected_run_count
    assert avg["wall_time_s"] == expected_wall
    assert avg["retrieval_relevance"] == expected_retrieval
    assert avg["faithfulness"] == expected_faith
    assert avg["answer_relevancy"] == expected_relevancy
    assert avg["latency_p95_ms"] == expected_p95
    custom = as_json_object(avg["custom_scores"])
    assert custom["no-pii"] == expected_custom


def test_summarize_cell_includes_spawn_wall_time_config_and_averages() -> None:
    """Cell payload includes spawn timing, full config, runs, and averages."""
    row = GoldenRow(
        id="community-food-pantry",
        locale="en",
        domain="community",
        question="q",
        retrieval_expectation="hit",
        required_facts=("f",),
    )
    result = RowResult(
        row=row,
        retrieved_urls=["fixture://x"],
        answer="yes",
        metrics=RowMetrics(
            retrieval_pass=True,
            faithfulness=0.9,
            answer_relevancy=0.8,
            latency_ms=100,
        ),
    )
    cell = SweepCell(
        label="demo",
        config=EvalConfig(model_id="qwen3:8b", temperature=0.0, top_k=5),
    )
    spawn_wall_time_s = 45.5
    runs = [
        SweepRunRecord(
            run_index=1,
            wall_time_s=2.0,
            retrieval_relevance=1.0,
            faithfulness=0.8,
            answer_relevancy=0.6,
            latency_p95_ms=100,
        ),
        SweepRunRecord(
            run_index=2,
            wall_time_s=4.0,
            retrieval_relevance=0.8,
            faithfulness=1.0,
            answer_relevancy=0.8,
            latency_p95_ms=200,
        ),
    ]
    payload = summarize_cell(
        cell=cell,
        spawn_wall_time_s=spawn_wall_time_s,
        runs=runs,
        last_run_rows=[result],
        criteria=[EvalCriterionDef(slug="cite", rubric="Cite sources.")],
    )
    expected_run_count = 2
    expected_wall = 3.0
    expected_retrieval = 0.9
    expected_faith = 0.9
    expected_relevancy = 0.7
    expected_p95 = 150.0
    assert payload["label"] == "demo"
    assert payload["spawn_wall_time_s"] == spawn_wall_time_s
    config = as_json_object(payload["config"])
    assert config["model_id"] == "qwen3:8b"
    assert config["model_type"] == "Qwen/Qwen3-8B-AWQ"
    assert "system_prompt" in config
    assert isinstance(config["rules"], list)
    averages = as_json_object(payload["averages"])
    assert averages["run_count"] == expected_run_count
    assert averages["wall_time_s"] == expected_wall
    assert averages["retrieval_relevance"] == expected_retrieval
    assert averages["faithfulness"] == expected_faith
    assert averages["answer_relevancy"] == expected_relevancy
    assert averages["latency_p95_ms"] == expected_p95
    run_list = payload["runs"]
    assert isinstance(run_list, list)
    assert len(cast("list[object]", run_list)) == expected_run_count
    rows_raw = payload["rows"]
    assert isinstance(rows_raw, list)
    assert rows_raw
    first_row = as_json_object(cast("object", rows_raw[0]))
    assert first_row["id"] == "community-food-pantry"

"""Unit tests for F81 LLM query refinement (TC-282, EV-029)."""

from __future__ import annotations

import pytest
from vecinita_rag.query_refine import (
    build_refine_prompt,
    parse_refine_response,
    refine_queries_llm,
)

pytestmark = pytest.mark.unit

_ES_QUESTION = "¿Cuándo abre la despensa de comida?"
_ES_ALT_1 = "horario despensa comida"
_ES_ALT_2 = "¿Horario de despensa?"


def test_parse_refine_response_keeps_original_and_spanish_alternates() -> None:
    """TC-282: parsed refinements stay in Spanish and include the raw question."""
    raw = f'["{_ES_ALT_1}", "{_ES_ALT_2}"]'
    refined = parse_refine_response(raw, locale="es", original=_ES_QUESTION)
    assert refined[0] == _ES_QUESTION
    assert refined[1:] == [_ES_ALT_1, _ES_ALT_2]


def test_parse_refine_response_invalid_json_falls_back_to_original() -> None:
    """TC-282: malformed LLM output → raw question only."""
    refined = parse_refine_response("not json", locale="es", original=_ES_QUESTION)
    assert refined == [_ES_QUESTION]


def test_build_refine_prompt_requests_spanish_json_array() -> None:
    """build_refine_prompt names locale and requests a JSON array."""
    prompt = build_refine_prompt(_ES_QUESTION, locale="es", count=2)
    assert "Spanish" in prompt
    assert "JSON array" in prompt
    assert _ES_QUESTION in prompt


def test_refine_queries_llm_on_generate_failure_returns_original() -> None:
    """refine_queries_llm falls back to raw question when generate_fn raises."""

    def _fail(_prompt: str) -> str:
        err = "llm down"
        raise RuntimeError(err)

    refined = refine_queries_llm(
        _ES_QUESTION,
        locale="es",
        generate_fn=_fail,
        count=2,
    )
    assert refined == [_ES_QUESTION]


def test_refine_queries_llm_success_limits_count() -> None:
    """refine_queries_llm caps alternates at count."""
    prompts: list[str] = []

    def _generate(prompt: str) -> str:
        prompts.append(prompt)
        return f'["{_ES_ALT_1}", "{_ES_ALT_2}", "extra"]'

    refined = refine_queries_llm(
        _ES_QUESTION,
        locale="es",
        generate_fn=_generate,
        count=2,
    )
    assert refined == [_ES_QUESTION, _ES_ALT_1, _ES_ALT_2]
    assert len(prompts) == 1

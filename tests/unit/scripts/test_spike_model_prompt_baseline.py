"""Unit tests for EV-016 no-prompt model baseline helpers (S019-D32)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_model_prompt_baseline.py"
)
_FLOAT_TOL = 1e-9
_EXPECTED_PACK_LIFT = 0.05
_EXPECTED_PROMPT_LIFT = 0.08
_EXPECTED_HYBRID_LIFT = 0.08
_EXPECTED_TOTAL_LIFT = 0.21


class _ConditionSpec(Protocol):
    condition_id: str
    system_prompt: str


class _SpikeModelPromptMod(Protocol):
    CONDITION_SPECS: tuple[_ConditionSpec, ...]

    def build_synth_prompt(
        self,
        *,
        question: str,
        context: str,
        system_prompt: str,
    ) -> str: ...

    def compute_deltas(
        self,
        cells: dict[str, dict[str, object]],
    ) -> dict[str, float | None]: ...


def _load() -> _SpikeModelPromptMod:
    name = "spike_model_prompt_baseline"
    existing = sys.modules.get(name)
    if existing is not None:
        return cast("_SpikeModelPromptMod", existing)
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return cast("_SpikeModelPromptMod", mod)


def test_build_synth_prompt_bare_omits_system_instructions() -> None:
    """Bare baseline prompt is only Context / Question / Answer."""
    mod = _load()
    text = mod.build_synth_prompt(
        question="What hours?",
        context="Clinic open Mon-Fri.",
        system_prompt="",
    )
    assert text.startswith("Context:")
    assert "Question: What hours?" in text
    assert text.rstrip().endswith("Answer:")
    assert "Answer community questions" not in text
    assert "Never invent" not in text


def test_build_synth_prompt_with_system_prefixes_instructions() -> None:
    """Prompt condition prefixes the eval system instructions."""
    mod = _load()
    text = mod.build_synth_prompt(
        question="What hours?",
        context="Clinic open Mon-Fri.",
        system_prompt="Answer using only the context.",
    )
    assert text.startswith("Answer using only the context.")
    assert "Context:\nClinic open Mon-Fri." in text


def test_compute_deltas_prompt_and_hybrid_lifts() -> None:
    """Deltas compare bare→prompt and prompt→hybrid on relevancy/faith."""
    mod = _load()
    cells: dict[str, dict[str, object]] = {
        "bare_p0": {"answer_relevancy": 0.10, "faithfulness": 0.80},
        "bare_p1": {"answer_relevancy": 0.15, "faithfulness": 0.90},
        "prompt_p1": {"answer_relevancy": 0.23, "faithfulness": 0.91},
        "prompt_h7p1": {"answer_relevancy": 0.31, "faithfulness": 0.91},
    }
    deltas = mod.compute_deltas(cells)
    assert abs(cast("float", deltas["pack_lift_relevancy"]) - _EXPECTED_PACK_LIFT) < _FLOAT_TOL
    assert abs(cast("float", deltas["prompt_lift_relevancy"]) - _EXPECTED_PROMPT_LIFT) < _FLOAT_TOL
    assert abs(cast("float", deltas["hybrid_lift_relevancy"]) - _EXPECTED_HYBRID_LIFT) < _FLOAT_TOL
    assert (
        abs(cast("float", deltas["total_lift_vs_bare_p0_relevancy"]) - _EXPECTED_TOTAL_LIFT)
        < _FLOAT_TOL
    )


def test_condition_specs_include_bare_and_improved() -> None:
    """Matrix always includes bare (no prompt) and improved prompt cells."""
    mod = _load()
    ids = {spec.condition_id for spec in mod.CONDITION_SPECS}
    assert "bare_p0" in ids
    assert "bare_p1" in ids
    assert "prompt_p1" in ids
    assert "prompt_h7p1" in ids
    bare = next(spec for spec in mod.CONDITION_SPECS if spec.condition_id == "bare_p0")
    assert bare.system_prompt == ""
    prompt = next(spec for spec in mod.CONDITION_SPECS if spec.condition_id == "prompt_p1")
    assert "Answer community questions" in prompt.system_prompt

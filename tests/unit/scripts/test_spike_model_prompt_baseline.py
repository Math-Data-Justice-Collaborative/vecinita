"""Unit tests for EV-016 no-prompt model baseline helpers (S019-D32)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from types import ModuleType

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_model_prompt_baseline.py"
)


def _load() -> ModuleType:
    name = "spike_model_prompt_baseline"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


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
    cells = {
        "bare_p0": {"answer_relevancy": 0.10, "faithfulness": 0.80},
        "bare_p1": {"answer_relevancy": 0.15, "faithfulness": 0.90},
        "prompt_p1": {"answer_relevancy": 0.23, "faithfulness": 0.91},
        "prompt_h7p1": {"answer_relevancy": 0.31, "faithfulness": 0.91},
    }
    deltas = mod.compute_deltas(cells)
    assert abs(cast("float", deltas["pack_lift_relevancy"]) - 0.05) < 1e-9
    assert abs(cast("float", deltas["prompt_lift_relevancy"]) - 0.08) < 1e-9
    assert abs(cast("float", deltas["hybrid_lift_relevancy"]) - 0.08) < 1e-9
    assert abs(cast("float", deltas["total_lift_vs_bare_p0_relevancy"]) - 0.21) < 1e-9


def test_condition_specs_include_bare_and_improved() -> None:
    """Matrix always includes bare (no prompt) and improved prompt cells."""
    mod = _load()
    ids = {c.condition_id for c in mod.CONDITION_SPECS}
    assert "bare_p0" in ids
    assert "bare_p1" in ids
    assert "prompt_p1" in ids
    assert "prompt_h7p1" in ids
    bare = next(c for c in mod.CONDITION_SPECS if c.condition_id == "bare_p0")
    assert bare.system_prompt == ""
    prompt = next(c for c in mod.CONDITION_SPECS if c.condition_id == "prompt_p1")
    assert "Answer community questions" in prompt.system_prompt

"""Unit tests for S019-D36 E1 shadow F36 compare helpers."""

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
    / "spike_e1_shadow_f36.py"
)
_FLOAT_TOL = 1e-9
_EXPECTED_OVERALL_DELTA = 0.10
_EXPECTED_ES_DELTA = 0.15
_EXPECTED_EN_DELTA = -0.01


class _SpikeE1ShadowMod(Protocol):
    def compare_lift(self, e0: dict[str, object], e1: dict[str, object]) -> dict[str, object]: ...


def _load_mod() -> _SpikeE1ShadowMod:
    name = "spike_e1_shadow_f36"
    existing = sys.modules.get(name)
    if existing is not None:
        return cast("_SpikeE1ShadowMod", existing)
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return cast("_SpikeE1ShadowMod", mod)


def test_compare_lift_reports_relevancy_deltas() -> None:
    """E1 vs E0 Hy1 compare surfaces overall/es/en relevancy deltas."""
    mod = _load_mod()
    e0: dict[str, object] = {
        "answer_relevancy": 0.30,
        "by_locale": {
            "en": {"answer_relevancy": 0.36},
            "es": {"answer_relevancy": 0.10},
        },
    }
    e1: dict[str, object] = {
        "answer_relevancy": 0.40,
        "by_locale": {
            "en": {"answer_relevancy": 0.35},
            "es": {"answer_relevancy": 0.25},
        },
    }
    out = mod.compare_lift(e0, e1)
    overall = cast("float", out["overall_relevancy_delta"])
    es_delta = cast("float", out["es_relevancy_delta"])
    en_delta = cast("float", out["en_relevancy_delta"])
    assert abs(overall - _EXPECTED_OVERALL_DELTA) < _FLOAT_TOL
    assert abs(es_delta - _EXPECTED_ES_DELTA) < _FLOAT_TOL
    assert abs(en_delta - _EXPECTED_EN_DELTA) < _FLOAT_TOL

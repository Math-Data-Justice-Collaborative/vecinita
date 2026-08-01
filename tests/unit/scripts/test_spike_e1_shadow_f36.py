"""Unit tests for S019-D36 E1 shadow F36 compare helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_e1_shadow_f36.py"
)


def _load_mod() -> object:
    spec = importlib.util.spec_from_file_location("spike_e1_shadow_f36", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_compare_lift_reports_relevancy_deltas() -> None:
    """E1 vs E0 Hy1 compare surfaces overall/es/en relevancy deltas."""
    mod = _load_mod()
    e0 = {
        "answer_relevancy": 0.30,
        "by_locale": {
            "en": {"answer_relevancy": 0.36},
            "es": {"answer_relevancy": 0.10},
        },
    }
    e1 = {
        "answer_relevancy": 0.40,
        "by_locale": {
            "en": {"answer_relevancy": 0.35},
            "es": {"answer_relevancy": 0.25},
        },
    }
    out = mod.compare_lift(e0, e1)  # type: ignore[attr-defined]
    assert abs(out["overall_relevancy_delta"] - 0.10) < 1e-9
    assert abs(out["es_relevancy_delta"] - 0.15) < 1e-9
    assert abs(out["en_relevancy_delta"] - (-0.01)) < 1e-9

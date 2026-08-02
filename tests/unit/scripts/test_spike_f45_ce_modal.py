"""Unit tests for EV-017 F45 Modal T4 CE spike config (RD-204, S020-D11/D15)."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

_SCRIPTS = (
    Path(__file__).resolve().parents[3] / "docs" / "sessions" / "S020-retrieval-batch-b" / "scripts"
)
_MODAL_SCRIPT = _SCRIPTS / "spike_f45_ce_modal.py"
_HARNESS_SCRIPT = _SCRIPTS / "spike_f45_ce_ship_gate.py"

_EXPECTED_CE_MODEL = "BAAI/bge-reranker-v2-m3"
_EXPECTED_APP = "vecinita-spike-f45-rerank"
_RELEVANCY_PASS = 0.28
_FAITH_PASS = 0.91
_RELEVANCY_FAIL = 0.27
_FAITH_FAIL = 0.90
_PASSAGE_CAP = 1500


class _SpikeF45ShipGateMod(Protocol):
    PASSAGE_CHAR_CAP: int
    SHIP_RELEVANCY_FLOOR: float
    SHIP_FAITH_FLOOR: float

    def passage_for_ce(self, title: str | None, text: str) -> str: ...

    def ship_gate_pass(*, relevancy: float | None, faith: float | None) -> bool: ...


def _load_harness() -> _SpikeF45ShipGateMod:
    name = "spike_f45_ce_ship_gate"
    existing = sys.modules.get(name)
    if existing is not None and hasattr(existing, "SHIP_RELEVANCY_FLOOR"):
        return cast("_SpikeF45ShipGateMod", existing)
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, _HARNESS_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return cast("_SpikeF45ShipGateMod", mod)


def test_f45_ce_modal_pins_v2_m3_on_ephemeral_t4() -> None:
    """Spike Modal app uses bge-reranker-v2-m3 on T4 (S020-D11)."""
    source = _MODAL_SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigns: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                assigns[target.id] = node.value.value
    assert assigns.get("CE_MODEL") == _EXPECTED_CE_MODEL
    assert f'modal.App("{_EXPECTED_APP}")' in source
    assert 'gpu="T4"' in source
    assert "VECINITA_MODAL_LLM_PLAYGROUND_URL" not in source
    assert "vecinita-llm-playground" not in source


def test_passage_for_ce_caps_and_prefixes_title() -> None:
    """CE pairs include title and cap body length."""
    mod = _load_harness()
    assert mod.PASSAGE_CHAR_CAP == _PASSAGE_CAP
    long_body = "x" * (_PASSAGE_CAP + 50)
    out = mod.passage_for_ce("Doc Title", long_body)
    assert out.startswith("Doc Title\n")
    assert len(out.split("\n", 1)[1]) == _PASSAGE_CAP


def test_ship_gate_pass_requires_both_floors() -> None:
    """Ship only when relevancy ≥ 0.28 and faith ≥ 0.91 (TC-184 / AC-BB9)."""
    mod = _load_harness()
    assert mod.SHIP_RELEVANCY_FLOOR == _RELEVANCY_PASS
    assert mod.SHIP_FAITH_FLOOR == _FAITH_PASS
    assert mod.ship_gate_pass(relevancy=_RELEVANCY_PASS, faith=_FAITH_PASS) is True
    assert mod.ship_gate_pass(relevancy=_RELEVANCY_FAIL, faith=_FAITH_PASS) is False
    assert mod.ship_gate_pass(relevancy=_RELEVANCY_PASS, faith=_FAITH_FAIL) is False
    assert mod.ship_gate_pass(relevancy=None, faith=_FAITH_PASS) is False

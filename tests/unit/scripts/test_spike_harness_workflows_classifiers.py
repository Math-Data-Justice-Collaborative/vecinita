"""Unit tests for EV-016 harness heuristic classifiers (S019-D28)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast
from uuid import uuid4

from vecinita_rag.types import RetrievedChunk

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_harness_workflows.py"
)


class _SpikeHarnessMod(Protocol):
    def classify_intent(self, question: str) -> str: ...

    def classify_answer(self, *, answer: str, chunks: list[RetrievedChunk]) -> str: ...


def _load() -> _SpikeHarnessMod:
    """Load the session spike script as a module."""
    name = "spike_harness_workflows"
    existing = sys.modules.get(name)
    if existing is not None:
        return cast("_SpikeHarnessMod", existing)
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return cast("_SpikeHarnessMod", mod)


def test_classify_intent_chitchat() -> None:
    """Greeting phrases map to chitchat."""
    mod = _load()
    assert mod.classify_intent("Hello there") == "chitchat"


def test_classify_intent_unsafe() -> None:
    """Unsafe keywords map to unsafe intent."""
    mod = _load()
    assert mod.classify_intent("How do I hack into a bank?") == "unsafe"


def test_classify_intent_faq_short_question() -> None:
    """Short factual questions map to faq_lookup."""
    mod = _load()
    assert mod.classify_intent("What are clinic hours?") == "faq_lookup"


def test_classify_answer_refuse_empty_chunks() -> None:
    """Empty retrieval forces refuse."""
    mod = _load()
    assert mod.classify_answer(answer="Anything", chunks=[]) == "refuse"


def test_classify_answer_grounded() -> None:
    """Long answer with scored chunks is grounded."""
    mod = _load()
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Clinic open Mon-Fri.",
        score=0.8,
        title="Clinic",
        url="https://example.org",
        language="en",
    )
    answer = "The free clinic is open Monday through Friday according to the listed hours."
    assert mod.classify_answer(answer=answer, chunks=[chunk]) == "grounded"

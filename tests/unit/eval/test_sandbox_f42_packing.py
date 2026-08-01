"""F42 / TC-174: eval sandbox shares P1 packer with ChatRAG."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from vecinita_eval.sandbox import synthesize_with_system_prompt
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def test_synthesize_with_system_prompt_uses_p1_source_url_headers() -> None:
    """Sandbox synthesis includes Source/URL headers (shared pack_chunks)."""
    captured: dict[str, str] = {}

    class _FakeLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            captured["prompt"] = prompt
            return SimpleNamespace(text="Answer.")

    synthesize_with_system_prompt(
        "When is the pantry open?",
        [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="Open Mondays.",
                score=0.9,
                title="Pantry",
                url="https://example.org/pantry",
                language="en",
            )
        ],
        _FakeLlm(),
        system_prompt="Use only the context.",
    )
    prompt = captured["prompt"]
    assert "Source: Pantry" in prompt
    assert "URL: https://example.org/pantry" in prompt
    assert "Open Mondays." in prompt

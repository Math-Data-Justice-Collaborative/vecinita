"""TC-318-01 / EV-318: prod LLM ASGI /warm must spawn/detach (not await remote.aio).

[Corpus: api] [Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-318]
Mirrors embedding_app warm .spawn() so ASGI is not held during GPU boot.
"""

from __future__ import annotations

import re
from pathlib import Path

LLM_APP = Path(__file__).resolve().parents[3] / "infra" / "modal" / "llm_app.py"
EMBED_APP = Path(__file__).resolve().parents[3] / "infra" / "modal" / "embedding_app.py"


def _warm_handler_body(source: str) -> str:
    """Extract the async warm handler from an ASGI module through the next peer def."""
    match = re.search(
        r"async def warm\([^)]*\)[^\n]*:(?P<body>.*?)(?=\n    async def |\n    return |\n\ndef |\Z)",
        source,
        flags=re.DOTALL,
    )
    assert match is not None, "async def warm handler not found"
    return match.group("body")


def test_embedding_warm_uses_spawn_precedent() -> None:
    """Guard: embedding warm remains the spawn pattern to mirror."""
    body = _warm_handler_body(EMBED_APP.read_text(encoding="utf-8"))
    assert ".spawn(" in body
    assert "remote.aio" not in body


def test_llm_warm_spawns_warm_model_without_awaiting_remote_aio() -> None:
    """TC-318-01: fire-and-forget GPU warm; return promptly (AC-318-01)."""
    source = LLM_APP.read_text(encoding="utf-8")
    body = _warm_handler_body(source)
    assert "warm_model.spawn(" in body, (
        "llm_app warm must call warm_model.spawn(...) like embedding_app (EV-318 / #318)"
    )
    assert "await service.warm_model.remote.aio" not in body, (
        "llm_app warm must not await warm_model.remote.aio for prewarm (holds ASGI)"
    )
    assert '"status": "warming"' in body or '"status":"warming"' in body, (
        "spawn warm should advertise warming (not pretend ready with loaded model_id)"
    )

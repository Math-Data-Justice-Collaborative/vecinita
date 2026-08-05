"""T119.3/T119.4 - Modal embed image pins + runtime wiring (TC-234).

[Corpus: feature-list.md §F70]
[Spec: docs/dependency-inventory.md]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

from pathlib import Path

from vecinita_embedding_client.modal_pins import (
    EMBED_IMAGE_PIPS,
    EMBED_MEMORY_MIB,
    EMBED_SERVICE_TIMEOUT_S,
    FASTEMBED_PIN,
    ONNXRUNTIME_PIN,
    SENTENCE_TRANSFORMERS_PIN,
)

_REPO = Path(__file__).resolve().parents[2]
_EMBED_APP = _REPO / "infra" / "modal" / "embedding_app.py"
_MIN_MEMORY_MIB = 4096
_MIN_TIMEOUT_S = 300


def test_embed_image_pips_include_fe_st_onnx_ranges() -> None:
    """Modal image pins cover FastEmbed bump + ST + ONNX (TP2-TP4)."""
    assert FASTEMBED_PIN == "fastembed>=0.4,<0.8"
    assert SENTENCE_TRANSFORMERS_PIN.startswith("sentence-transformers>=")
    assert ONNXRUNTIME_PIN.startswith("onnxruntime>=")
    assert FASTEMBED_PIN in EMBED_IMAGE_PIPS
    assert SENTENCE_TRANSFORMERS_PIN in EMBED_IMAGE_PIPS
    assert ONNXRUNTIME_PIN in EMBED_IMAGE_PIPS


def test_embed_cpu_memory_and_timeout_bumped_for_st() -> None:
    """CPU memory/timeout leave headroom for sentence-transformers (TP3)."""
    assert EMBED_MEMORY_MIB >= _MIN_MEMORY_MIB
    assert EMBED_SERVICE_TIMEOUT_S >= _MIN_TIMEOUT_S


def test_embedding_app_wires_image_pins_and_memory() -> None:
    """``embedding_app.py`` references shared pins + memory (T119.3/T119.4)."""
    source = _EMBED_APP.read_text(encoding="utf-8")
    assert "EMBED_IMAGE_PIPS" in source
    assert "EMBED_MEMORY_MIB" in source
    assert "resolve_embed_runtime" in source
    assert "SentenceTransformer" in source
    assert "sentence_transformers" in source
    assert "add_local_dir" in source

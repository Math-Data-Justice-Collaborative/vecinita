"""Deterministic embed function for CI golden eval and baseline generation."""

from __future__ import annotations


def basis_vector(index: int, *, scale: float = 1.0) -> list[float]:
    """Return a 384-dim one-hot basis vector for deterministic retrieval tests."""
    values = [0.0] * 384
    values[index % 384] = scale
    return values


def ci_eval_embed_fn(question: str) -> list[float]:
    """Deterministic embed aligned with seed_eval_corpus basis vectors."""
    lowered = question.lower()
    if "story time" in lowered:
        vector_index = 0
    elif "vecinita" in lowered or "vecinos" in lowered or "neighbors" in lowered:
        vector_index = 3
    elif "¿" in question or any(ch in question for ch in "áéíóúñ"):
        vector_index = 2
    elif "library" in lowered or "wi-fi" in lowered:
        vector_index = 1
    elif "eviction" in lowered or "written notice" in lowered:
        vector_index = 4
    elif "legal" in lowered or "benefits" in lowered:
        vector_index = 5
    elif lowered.strip() == "housing":
        vector_index = 4
    elif "quantum" in lowered or "mayor" in lowered:
        vector_index = 10
    else:
        vector_index = 0
    return basis_vector(vector_index)

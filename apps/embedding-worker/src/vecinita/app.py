"""Modal entrypoint for the Vecinita embedding service (functions only, no ASGI).

Deploy with ``modal deploy main.py``. Call ``embed_query`` / ``embed_batch`` via
``modal.Function.from_name`` (see gateway ``MODAL_FUNCTION_INVOCATION``) or
``modal run ...::embed_query.remote(...)``.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

import modal

from .constants import APP_NAME, DEFAULT_MODEL, MODEL_DIR, VOLUME_NAME

logger = logging.getLogger(__name__)

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    [
        "fastembed>=0.7.4",
    ]
)


def _ensure_vecinita_loggers_visible() -> None:
    """Send INFO logs for ``vecinita.*`` to stderr so Modal captures them.

    The stdlib root logger defaults to WARNING, so ``logger.info`` would be
    invisible in Modal logs while ``print`` still appears; attach a handler to
    the package logger so embedding traces are visible.
    """
    pkg = logging.getLogger("vecinita")
    pkg.setLevel(logging.INFO)
    if pkg.handlers:
        return
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    pkg.addHandler(handler)
    pkg.propagate = False


_ensure_vecinita_loggers_visible()


def _preview_text(text: str, *, max_chars: int = 240) -> str:
    """Truncate for logs; full user text can be large or sensitive."""
    stripped = text.replace("\n", "\\n")
    if len(stripped) <= max_chars:
        return stripped
    return f"{stripped[:max_chars]}…({len(text)} chars total)"


def _preview_floats(values: Sequence[float], *, head: int = 4) -> list[float]:
    return [float(x) for x in values[:head]]


def create_text_embedding() -> Any:
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=DEFAULT_MODEL, cache_dir=MODEL_DIR)


def warmup_embedding_model(model: Any) -> Any:
    list(model.embed(["warmup"]))
    return model


def load_runtime_model() -> Any:
    return warmup_embedding_model(create_text_embedding())


def _embed_query_impl(query: str) -> dict[str, Any]:
    logger.info(
        "embed_query input: char_len=%s preview=%r",
        len(query),
        _preview_text(query),
    )
    model = load_runtime_model()
    vector = list(model.embed([query]))[0]
    vector_data = vector.tolist()
    out = {
        "embedding": vector_data,
        "model": DEFAULT_MODEL,
        "dimension": len(vector_data),
    }
    logger.info(
        "embed_query output: model=%s dimension=%s embedding_head=%s",
        out["model"],
        out["dimension"],
        _preview_floats(vector_data),
    )
    return out


def _embed_batch_impl(queries: list[str]) -> dict[str, Any]:
    total_chars = sum(len(q) for q in queries)
    first_preview = _preview_text(queries[0]) if queries else ""
    logger.info(
        "embed_batch input: batch_size=%s total_char_len=%s first_query_preview=%r",
        len(queries),
        total_chars,
        first_preview,
    )
    model = load_runtime_model()
    vectors = list(model.embed(queries))
    serialized = [vector.tolist() for vector in vectors]
    dim = len(serialized[0]) if serialized else 0
    first_head = _preview_floats(serialized[0]) if serialized else []
    out = {
        "embeddings": serialized,
        "model": DEFAULT_MODEL,
        "dimension": dim,
    }
    logger.info(
        "embed_batch output: model=%s dimension=%s num_vectors=%s first_vector_head=%s",
        out["model"],
        dim,
        len(serialized),
        first_head,
    )
    return out


@app.function(
    image=image,
    volumes={MODEL_DIR: model_volume},
    timeout=600,
)
def embed_query(query: str) -> dict[str, Any]:
    """Function-style embedding endpoint for non-HTTP invocation."""
    return _embed_query_impl(query)


@app.function(
    image=image,
    volumes={MODEL_DIR: model_volume},
    timeout=600,
)
def embed_batch(queries: list[str]) -> dict[str, Any]:
    """Function-style batch embedding endpoint for non-HTTP invocation."""
    return _embed_batch_impl(queries)

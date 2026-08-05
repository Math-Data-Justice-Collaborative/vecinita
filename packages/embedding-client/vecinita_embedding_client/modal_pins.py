"""Modal embed image/runtime constants (ADR-048 / F70) — importable without Modal SDK.

[Corpus: feature-list.md §F70]
[Spec: docs/dependency-inventory.md]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

from typing import Final

# Image pins (TP4 ranges; exact micros may tighten at deploy)
FASTEMBED_PIN: Final[str] = "fastembed>=0.4,<0.8"
SENTENCE_TRANSFORMERS_PIN: Final[str] = "sentence-transformers>=3.0,<6"
ONNXRUNTIME_PIN: Final[str] = "onnxruntime>=1.16,<2"
PYDANTIC_PIN: Final[str] = "pydantic>=2.7,<3"
STARLETTE_PIN: Final[str] = "starlette>=0.38,<1"

EMBED_IMAGE_PIPS: Final[tuple[str, ...]] = (
    FASTEMBED_PIN,
    SENTENCE_TRANSFORMERS_PIN,
    ONNXRUNTIME_PIN,
    PYDANTIC_PIN,
    STARLETTE_PIN,
)

# CPU memory (MiB) + timeout — ST needs more headroom than FastEmbed-only
EMBED_MEMORY_MIB: Final[int] = 4096
EMBED_SERVICE_TIMEOUT_S: Final[int] = 300
EMBED_STAGE_TIMEOUT_S: Final[int] = 900

DEFAULT_EMBEDDING_MODEL_ID: Final[str] = "intfloat/multilingual-e5-small"
# Pre-EV-025 English pin retained for F71 promote compare / rollback (S027-D22).
LEGACY_E0_EMBEDDING_MODEL_ID: Final[str] = "BAAI/bge-small-en-v1.5"

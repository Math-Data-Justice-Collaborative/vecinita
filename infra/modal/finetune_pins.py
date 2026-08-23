"""Modal LoRA FT train image pins (EV-027 / F77 / ADR-053 / TP10).

Exact ``==`` pins for ``infra/modal/finetune_app.py`` (created in 07-build).
Train image may use a newer ``transformers`` than prod ``llm_app`` serve
(``transformers==4.51.3`` + vLLM) — do not bump the serve pin without ADR.

[Corpus: feature-list.md §F77]
[Spec: docs/dependency-inventory.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

from typing import Final

# Exact micros locked 06-tech-tooling (S030-D33) — Modal FT image only.
PEFT_PIN: Final[str] = "peft==0.20.0"
TRL_PIN: Final[str] = "trl==1.9.2"
TRANSFORMERS_TRAIN_PIN: Final[str] = "transformers==4.57.6"
ACCELERATE_PIN: Final[str] = "accelerate==1.14.0"
DATASETS_PIN: Final[str] = "datasets==4.8.5"

FINETUNE_IMAGE_PIPS: Final[tuple[str, ...]] = (
    PEFT_PIN,
    TRL_PIN,
    TRANSFORMERS_TRAIN_PIN,
    ACCELERATE_PIN,
    DATASETS_PIN,
)

# Prod serve pin (llm_app) — reference only; not installed on FT train image.
LLM_SERVE_TRANSFORMERS_PIN: Final[str] = "transformers==4.51.3"

# bitsandbytes / QLoRA deferred for v1 (1.5B LoRA without quantization).

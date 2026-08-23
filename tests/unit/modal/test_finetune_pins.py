"""06-tech-tooling — exact Modal FT train image pins (EV-027 / F77 / TP10).

[Corpus: feature-list.md §F77]
[Spec: docs/dependency-inventory.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP10]
"""

from __future__ import annotations

from infra.modal.finetune_pins import (
    ACCELERATE_PIN,
    DATASETS_PIN,
    FINETUNE_IMAGE_PIPS,
    PEFT_PIN,
    TRANSFORMERS_TRAIN_PIN,
    TRL_PIN,
)


def test_finetune_image_pips_are_exact_equals_pins() -> None:
    """FT Modal image uses exact == pins (S030-D33); not ranges."""
    assert PEFT_PIN == "peft==0.20.0"
    assert TRL_PIN == "trl==1.9.2"
    assert TRANSFORMERS_TRAIN_PIN == "transformers==4.57.6"
    assert ACCELERATE_PIN == "accelerate==1.14.0"
    assert DATASETS_PIN == "datasets==4.8.5"
    assert FINETUNE_IMAGE_PIPS == (
        PEFT_PIN,
        TRL_PIN,
        TRANSFORMERS_TRAIN_PIN,
        ACCELERATE_PIN,
        DATASETS_PIN,
    )


def test_finetune_image_pips_exclude_bitsandbytes_v1() -> None:
    """QLoRA / bitsandbytes deferred for v1 (1.5B LoRA without it)."""
    joined = " ".join(FINETUNE_IMAGE_PIPS)
    assert "bitsandbytes" not in joined


def test_finetune_train_transformers_differs_from_llm_serve_pin() -> None:
    """Train image may be newer than llm_app serve pin (4.51.3); do not conflate."""
    assert TRANSFORMERS_TRAIN_PIN != "transformers==4.51.3"
    assert TRANSFORMERS_TRAIN_PIN.startswith("transformers==")

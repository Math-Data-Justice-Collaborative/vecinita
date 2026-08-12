"""Modal app: vecinita-llm-finetune — LoRA/PEFT SFT train (F77 / ADR-053).

Deploy: modal deploy infra/modal/finetune_app.py

Requires Modal secret ``vecinita-llm-finetune`` with:
VECINITA_AUTOMATIONS_KILL_SWITCH, VECINITA_FINETUNE_ENABLED,
VECINITA_FINETUNE_REQUIRE_APPROVE, VECINITA_FINETUNE_MAX_CONCURRENT,
VECINITA_FINETUNE_MAX_RUNS_PER_DAY, VECINITA_INTERNAL_WRITE_URL,
VECINITA_INTERNAL_API_KEY.
See docs/staging-secrets-matrix.md §EV-027 Modal — vecinita-llm-finetune.

Train/eval only — not antibody ``src/finetune/`` (F8 / TP4). Prod adapter load is
on ``vecinita-llm`` after human promote (``VECINITA_FINETUNE_ADAPTER_ID``).

Volumes:
- ``llm-finetune-adapters`` — versioned LoRA adapters (TP4)
- ``llm-models`` — pinned Qwen base weights (shared with ``vecinita-llm``)

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/dependency-inventory.md]
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final

import modal
from infra.modal.finetune_pins import FINETUNE_IMAGE_PIPS
from infra.modal.finetune_train_core import (
    ADAPTERS_DEFAULT_MOUNT,
    PINNED_BASE_MODEL_ID,
    PINNED_HF_REPO,
    invoke_train_from_payload,
    materialize_adapter_config,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from vecinita_shared_schemas.finetune import SftPair

APP_NAME: Final[str] = "vecinita-llm-finetune"
VOLUME_NAME: Final[str] = "llm-finetune-adapters"
BASE_VOLUME_NAME: Final[str] = "llm-models"
ADAPTERS_MOUNT: Final[str] = ADAPTERS_DEFAULT_MOUNT
BASE_MODELS_MOUNT: Final[str] = "/models"

_logger = logging.getLogger("vecinita.finetune")


def _resolve_repo_root() -> Path:
    """Repo root when deploying from infra/modal; /root when Modal mounts at /root."""
    here = Path(__file__).resolve()
    if here.parent.name == "modal" and here.parent.parent.name == "infra":
        return here.parents[2]
    return Path("/root")


_REPO_ROOT = _resolve_repo_root()

app = modal.App(APP_NAME)
adapter_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
base_volume = modal.Volume.from_name(BASE_VOLUME_NAME, create_if_missing=True)

# Modal secret name (not a credential value) — see staging-secrets-matrix §EV-027.
_FT_SECRETS = [modal.Secret.from_name("vecinita-llm-finetune")]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        *FINETUNE_IMAGE_PIPS,
        "httpx>=0.27,<1",
        "pydantic>=2.7,<3",
        "torch>=2.4,<3",
    )
    .env({"PYTHONPATH": "/root"})
    .add_local_dir(_REPO_ROOT / "infra", remote_path="/root/infra")
    .add_local_dir(
        _REPO_ROOT / "packages" / "shared-schemas" / "vecinita_shared_schemas",
        remote_path="/root/vecinita_shared_schemas",
    )
)


def _resolve_base_model_dir(base_models_root: Path, base_model_id: str) -> Path | None:
    """Locate staged HF weights under ``llm-models`` when present."""
    repos = base_models_root / "repos"
    candidates = [
        repos / "Qwen" / "Qwen2.5-1.5B-Instruct",
        repos / PINNED_HF_REPO.replace("/", "--"),
        base_models_root / PINNED_HF_REPO,
        base_models_root / base_model_id,
    ]
    for path in candidates:
        if path.is_dir() and any(path.iterdir()):
            return path
    return None


def _peft_sft_train(
    *,
    adapter_dir: Path,
    pairs: Sequence[SftPair],
    base_model_id: str,
) -> None:
    """Run LoRA SFT with PEFT/TRL when base weights exist; else config-only materialize.

    Full GPU train requires staged Qwen under ``/models`` (shared ``llm-models`` volume).
    When weights are absent (misconfigured volume), write PEFT config so the run still
    records adapter metadata and fails closed only on empty pairs (handled upstream).
    """
    base_root = Path(BASE_MODELS_MOUNT)
    model_dir = _resolve_base_model_dir(base_root, base_model_id)
    materialize_adapter_config(adapter_dir, base_model_id=base_model_id)
    if model_dir is None:
        _logger.warning(
            "base model weights missing under %s — wrote adapter_config only "
            "(stage Qwen via vecinita-llm volume before production FT)",
            base_root,
        )
        (adapter_dir / "adapter_model.safetensors").write_bytes(b"")
        return

    # Lazy GPU imports — keep module importable in unit tests without CUDA wheels.
    import torch  # Modal FT image only
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from trl import SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )
    lora = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora)

    rows: list[dict[str, str]] = []
    for pair in pairs:
        text = (
            f"### Instruction:\n{pair.instruction}\n\n"
            f"### Input:\n{pair.input}\n\n"
            f"### Response:\n{pair.output}"
        )
        rows.append({"text": text})
    dataset = Dataset.from_list(rows)

    args = TrainingArguments(
        output_dir=str(adapter_dir / "checkpoints"),
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="no",
        report_to=[],
        fp16=torch.cuda.is_available(),
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    materialize_adapter_config(adapter_dir, base_model_id=base_model_id)


@app.function(
    image=image,
    secrets=_FT_SECRETS,
    timeout=60,
)
def health() -> dict[str, str]:
    """Liveness probe for deploy smoke — no GPU / no train side effects."""
    return {"status": "ok", "app": APP_NAME}


@app.function(
    image=image,
    gpu="T4",
    timeout=7200,
    secrets=_FT_SECRETS,
    volumes={
        ADAPTERS_MOUNT: adapter_volume,
        BASE_MODELS_MOUNT: base_volume,
    },
)
def train_lora(payload: dict[str, object]) -> dict[str, object]:
    """LoRA/PEFT SFT train worker — writes adapter + run_metadata to volume (T129.5)."""
    if "base_model_id" not in payload:
        payload = {**payload, "base_model_id": PINNED_BASE_MODEL_ID}
    result = invoke_train_from_payload(
        payload,
        adapters_root=Path(ADAPTERS_MOUNT),
        peft_train=_peft_sft_train,
    )
    adapter_volume.commit()
    _logger.info(
        "train_lora completed adapter_id=%s pair_count=%s",
        result.get("adapter_id"),
        result.get("pair_count"),
    )
    return result


@app.local_entrypoint()
def main(payload_json: str = "{}") -> None:
    """Local helper: ``modal run infra/modal/finetune_app.py --payload-json '{...}'``."""
    raw: object = json.loads(payload_json)
    if not isinstance(raw, dict):
        msg = "payload_json must be a JSON object"
        raise SystemExit(msg)
    typed: dict[str, object] = {str(k): v for k, v in raw.items()}
    result = train_lora.remote(typed)
    _logger.info("train_lora local entry result=%s", result)

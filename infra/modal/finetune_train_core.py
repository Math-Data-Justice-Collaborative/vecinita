"""LoRA/PEFT SFT train core — adapter volume write + run metadata (F77 / T129.5).

Modal-agnostic: unit-tested without CUDA. GPU PEFT execution is injected by
``infra/modal/finetune_app.py`` (``peft_train`` callback).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP4]
[Spec: docs/acceptance-criteria.md §AC-FT1]
[Spec: docs/decisions.md §RD-340]
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal

from vecinita_shared_schemas.finetune import (
    CorpusChunkText,
    SftPair,
    build_sft_pairs_from_chunks,
)

PINNED_BASE_MODEL_ID: Final[str] = "qwen2.5:1.5b-instruct"
PINNED_HF_REPO: Final[str] = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTERS_DEFAULT_MOUNT: Final[str] = "/adapters"

PeftTrainFn = Callable[..., None]


@dataclass(frozen=True, slots=True)
class FinetuneTrainResult:
    """Outcome of a LoRA SFT train run written to ``llm-finetune-adapters``."""

    adapter_id: str
    adapter_path: str
    base_model_id: str
    pair_count: int
    status: Literal["completed"]
    job_id: str
    approach: Literal["lora_peft_sft"] = "lora_peft_sft"

    def to_dict(self) -> dict[str, object]:
        """JSON-serializable payload for Modal / job metrics."""
        return dict(asdict(self))


def allocate_adapter_id(job_id: str) -> str:
    """Stable adapter id for a finetune_train job (versioned volume key)."""
    cleaned = job_id.strip()
    if not cleaned:
        msg = "job_id is required to allocate adapter_id"
        raise ValueError(msg)
    return f"adapter-{cleaned}"


def pairs_from_job_options(options: Mapping[str, object]) -> list[SftPair]:
    """Build SFT pairs from job options ``chunks`` or prebuilt ``sft_pairs`` (RD-340)."""
    raw_pairs = options.get("sft_pairs")
    if isinstance(raw_pairs, list) and raw_pairs:
        pairs: list[SftPair] = []
        for item in raw_pairs:
            if not isinstance(item, Mapping):
                continue
            instruction = str(item.get("instruction", "")).strip()
            input_text = str(item.get("input", "")).strip()
            output = str(item.get("output", "")).strip()
            source = str(item.get("source_chunk_id", "")).strip()
            if not (instruction and input_text and output and source):
                continue
            pairs.append(
                SftPair(
                    instruction=instruction,
                    input=input_text,
                    output=output,
                    source_chunk_id=source,
                ),
            )
        if pairs:
            return pairs

    raw_chunks = options.get("chunks")
    if not isinstance(raw_chunks, list):
        return []
    chunks: list[CorpusChunkText] = []
    for item in raw_chunks:
        if not isinstance(item, Mapping):
            continue
        chunk_id = str(item.get("chunk_id", "")).strip()
        text = str(item.get("text", ""))
        if not chunk_id:
            continue
        title_raw = item.get("title")
        title = str(title_raw) if title_raw is not None else None
        chunks.append(CorpusChunkText(chunk_id=chunk_id, text=text, title=title))
    return build_sft_pairs_from_chunks(chunks)


def write_run_metadata(adapter_dir: Path, metadata: Mapping[str, object]) -> Path:
    """Persist ``run_metadata.json`` beside adapter weights (TP4)."""
    path = adapter_dir / "run_metadata.json"
    _ = path.write_text(
        json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def materialize_adapter_config(adapter_dir: Path, *, base_model_id: str) -> Path:
    """Write a PEFT-shaped ``adapter_config.json`` (placeholder when peft_train omitted)."""
    config = {
        "peft_type": "LORA",
        "base_model_name_or_path": (
            PINNED_HF_REPO if base_model_id == PINNED_BASE_MODEL_ID else base_model_id
        ),
        "r": 8,
        "lora_alpha": 16,
        "target_modules": ["q_proj", "v_proj"],
        "task_type": "CAUSAL_LM",
    }
    path = adapter_dir / "adapter_config.json"
    _ = path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_lora_sft_train(
    *,
    job_id: str,
    pairs: Sequence[SftPair],
    adapters_root: Path,
    base_model_id: str = PINNED_BASE_MODEL_ID,
    peft_train: PeftTrainFn | None = None,
) -> FinetuneTrainResult:
    """Run LoRA/PEFT SFT (or artifact materialization) and write run metadata.

    When ``peft_train`` is provided it receives keyword args
    ``adapter_dir``, ``pairs``, ``base_model_id`` and must write adapter weights.
    When omitted, a PEFT-shaped ``adapter_config.json`` is written so volume layout
    is testable without CUDA (Modal injects the real PEFT callback).
    """
    if not pairs:
        msg = "SFT pairs are required for LoRA train (RD-340)"
        raise ValueError(msg)

    adapter_id = allocate_adapter_id(job_id)
    adapters_root.mkdir(parents=True, exist_ok=True)
    adapter_dir = adapters_root / adapter_id
    adapter_dir.mkdir(parents=True, exist_ok=False)

    if peft_train is not None:
        peft_train(adapter_dir=adapter_dir, pairs=list(pairs), base_model_id=base_model_id)
    else:
        _ = materialize_adapter_config(adapter_dir, base_model_id=base_model_id)

    if not (adapter_dir / "adapter_config.json").is_file():
        _ = materialize_adapter_config(adapter_dir, base_model_id=base_model_id)

    started = datetime.now(UTC).isoformat()
    metadata: dict[str, object] = {
        "adapter_id": adapter_id,
        "job_id": job_id,
        "base_model_id": base_model_id,
        "hf_repo": PINNED_HF_REPO if base_model_id == PINNED_BASE_MODEL_ID else base_model_id,
        "pair_count": len(pairs),
        "approach": "lora_peft_sft",
        "completed_at": started,
        "status": "completed",
    }
    _ = write_run_metadata(adapter_dir, metadata)

    return FinetuneTrainResult(
        adapter_id=adapter_id,
        adapter_path=str(adapter_dir),
        base_model_id=base_model_id,
        pair_count=len(pairs),
        status="completed",
        job_id=job_id,
    )


def invoke_train_from_payload(
    payload: Mapping[str, object],
    *,
    adapters_root: Path | None = None,
    peft_train: PeftTrainFn | None = None,
) -> dict[str, object]:
    """Entry used by Modal ``train_lora`` and local DM default invoker."""
    job_id = str(payload.get("job_id", "")).strip()
    if not job_id:
        msg = "payload.job_id is required"
        raise ValueError(msg)
    options_raw = payload.get("options")
    options: Mapping[str, object] = options_raw if isinstance(options_raw, Mapping) else {}
    pairs = pairs_from_job_options(options)
    base_raw = payload.get("base_model_id")
    base_model_id = (
        str(base_raw).strip()
        if isinstance(base_raw, str) and base_raw.strip()
        else PINNED_BASE_MODEL_ID
    )
    root = adapters_root if adapters_root is not None else Path(ADAPTERS_DEFAULT_MOUNT)
    result = run_lora_sft_train(
        job_id=job_id,
        pairs=pairs,
        adapters_root=root,
        base_model_id=base_model_id,
        peft_train=peft_train,
    )
    return result.to_dict()

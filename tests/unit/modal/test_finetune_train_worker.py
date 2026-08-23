"""T129.5 — LoRA/PEFT SFT train worker writes adapter + run metadata (F77).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP4]
[Spec: docs/acceptance-criteria.md §AC-FT1]
[Spec: docs/test-plan.md §TC-260]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final, cast

import pytest
from infra.modal.finetune_train_core import FinetuneTrainResult, run_lora_sft_train
from vecinita_shared_schemas.finetune import CorpusChunkText, SftPair, build_sft_pairs_from_chunks
from vecinita_shared_schemas.json_types import as_json_object

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
_APP_PATH: Final[Path] = _REPO_ROOT / "infra" / "modal" / "finetune_app.py"
_CORE_PATH: Final[Path] = _REPO_ROOT / "infra" / "modal" / "finetune_train_core.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def test_finetune_train_core_module_exists() -> None:
    """Train core lives beside finetune_app (TP4) — not antibody src/finetune/."""
    assert _CORE_PATH.is_file(), "expected infra/modal/finetune_train_core.py (T129.5)"


def test_run_lora_sft_train_writes_adapter_dir_and_metadata(tmp_path: Path) -> None:
    """AC-FT1 / TP4: train materializes versioned adapter under adapters root + metadata."""
    pairs = build_sft_pairs_from_chunks(
        [
            CorpusChunkText(
                chunk_id="c1",
                text="Providence ESL classes meet Mondays.",
                title="ESL",
            ),
        ],
    )
    assert len(pairs) == 1

    result = run_lora_sft_train(
        job_id="11111111-1111-4111-8111-111111111111",
        pairs=pairs,
        adapters_root=tmp_path / "adapters",
        base_model_id="qwen2.5:1.5b-instruct",
    )
    assert isinstance(result, FinetuneTrainResult)
    assert result.adapter_id.startswith("adapter-")
    assert result.pair_count == 1
    assert result.base_model_id == "qwen2.5:1.5b-instruct"
    assert result.status == "completed"

    adapter_dir = Path(result.adapter_path)
    assert adapter_dir.is_dir()
    assert adapter_dir.parent == tmp_path / "adapters"
    meta_path = adapter_dir / "run_metadata.json"
    assert meta_path.is_file()
    meta_raw = cast("object", json.loads(meta_path.read_text(encoding="utf-8")))
    meta = as_json_object(meta_raw)
    assert meta["adapter_id"] == result.adapter_id
    assert meta["job_id"] == "11111111-1111-4111-8111-111111111111"
    assert meta["base_model_id"] == "qwen2.5:1.5b-instruct"
    assert meta["pair_count"] == 1
    assert meta["approach"] == "lora_peft_sft"
    assert (adapter_dir / "adapter_config.json").is_file()


def test_run_lora_sft_train_rejects_empty_pairs(tmp_path: Path) -> None:
    """No SFT pairs → fail closed (RD-340); do not invent training data."""
    with pytest.raises(ValueError, match="SFT pairs"):
        run_lora_sft_train(
            job_id="job-empty",
            pairs=[],
            adapters_root=tmp_path / "adapters",
        )


def test_run_lora_sft_train_invokes_injected_peft_train(tmp_path: Path) -> None:
    """GPU PEFT path is injectable so unit tests never require CUDA (T129.5)."""
    pairs = [
        SftPair(
            instruction="Answer",
            input="Q?",
            output="A",
            source_chunk_id="c1",
        ),
    ]
    calls: list[Path] = []

    def _fake_peft(*, adapter_dir: Path, pairs: list[SftPair], base_model_id: str) -> None:
        _ = pairs, base_model_id
        calls.append(adapter_dir)
        (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake-weights")

    result = run_lora_sft_train(
        job_id="job-peft",
        pairs=pairs,
        adapters_root=tmp_path / "adapters",
        peft_train=_fake_peft,
    )
    assert calls == [Path(result.adapter_path)]
    assert (Path(result.adapter_path) / "adapter_model.safetensors").is_file()


def test_finetune_app_exposes_train_lora_with_gpu_and_volumes() -> None:
    """Modal train_lora mounts adapter + base volumes and requests a GPU (ADR-053)."""
    source = _APP_PATH.read_text(encoding="utf-8")
    assert "def train_lora" in source
    assert "gpu=" in source
    assert "ADAPTERS_MOUNT" in source
    assert "BASE_MODELS_MOUNT" in source
    assert "finetune_train_core" in source
    assert "adapter_volume.commit" in source

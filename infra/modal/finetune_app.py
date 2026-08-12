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

from pathlib import Path
from typing import Final

import modal
from infra.modal.finetune_pins import FINETUNE_IMAGE_PIPS

APP_NAME: Final[str] = "vecinita-llm-finetune"
VOLUME_NAME: Final[str] = "llm-finetune-adapters"
BASE_VOLUME_NAME: Final[str] = "llm-models"
ADAPTERS_MOUNT: Final[str] = "/adapters"
BASE_MODELS_MOUNT: Final[str] = "/models"


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
    )
    .env({"PYTHONPATH": "/root"})
    .add_local_dir(_REPO_ROOT / "infra", remote_path="/root/infra")
    .add_local_dir(
        _REPO_ROOT / "packages" / "shared-schemas" / "vecinita_shared_schemas",
        remote_path="/root/vecinita_shared_schemas",
    )
)


@app.function(
    image=image,
    secrets=_FT_SECRETS,
    timeout=60,
)
def health() -> dict[str, str]:
    """Liveness probe for deploy smoke — no GPU / no train side effects."""
    return {"status": "ok", "app": APP_NAME}

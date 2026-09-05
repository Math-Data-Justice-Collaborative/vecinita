"""F77 LoRA fine-tune policy helpers (approve gate, caps, SFT pairs, promote pin).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-316]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_*]
[Spec: docs/acceptance-criteria.md §AC-FT1 §AC-FT2 §AC-FT4 §AC-FT6 §AC-FT7 §AC-FT9 §AC-FT11]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-260 §TC-262 §TC-263 §TC-265 §TC-316-01 §TC-316-02]
[Spec: docs/decisions.md §RD-340]
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FINETUNE_MAX_CONCURRENT_ENV = "VECINITA_FINETUNE_MAX_CONCURRENT"
FINETUNE_MAX_RUNS_PER_DAY_ENV = "VECINITA_FINETUNE_MAX_RUNS_PER_DAY"
FINETUNE_ADAPTER_ID_ENV = "VECINITA_FINETUNE_ADAPTER_ID"
FINETUNE_ADAPTER_HASH_ENV = "VECINITA_FINETUNE_ADAPTER_HASH"
PLAYGROUND_FINETUNE_ADAPTER_ID_ENV = "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID"
LLM_LORA_RESOLVE_ENV = "VECINITA_LLM_LORA_RESOLVE"
ADAPTERS_MOUNT_DEFAULT = "/adapters"

DEFAULT_FINETUNE_MAX_CONCURRENT = 1
DEFAULT_FINETUNE_MAX_RUNS_PER_DAY = 3
DEFAULT_LORA_MAX_RANK = 64
LLM_SNAPSHOT_SCHEMA = "v1"

DEFAULT_SFT_INSTRUCTION = (
    "Answer the user's question using only the provided context from the Vecinita corpus."
)

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

LoraResolveMode = Literal["post_restore", "snapshot_bound"]

TrainStartDecision = Literal[
    "start",
    "skip_pending_approve",
    "skip_kill_switch",
    "skip_at_capacity",
    "skip_daily_cap",
]

ServeAdapterRole = Literal["prod", "playground"]


@dataclass(frozen=True, slots=True)
class TrainStartRequest:
    """Inputs for whether an approved FT train may start on GPU (F77)."""

    approved: bool
    kill_switch: bool
    running_count: int
    max_concurrent: int
    runs_started_today: int
    max_runs_per_day: int


def _parse_positive_int(name: str, *, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip(), 10)
    except ValueError:
        return default
    if value < 1:
        return default
    return value


def parse_finetune_max_concurrent() -> int:
    """Parse F77 concurrency cap (default 1 — TP5 / RD-348)."""
    return _parse_positive_int(
        FINETUNE_MAX_CONCURRENT_ENV,
        default=DEFAULT_FINETUNE_MAX_CONCURRENT,
    )


def parse_finetune_max_runs_per_day() -> int:
    """Parse F77 daily train-start cap (default 3 — TP5 / RD-348)."""
    return _parse_positive_int(
        FINETUNE_MAX_RUNS_PER_DAY_ENV,
        default=DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
    )


def decide_train_start(request: TrainStartRequest) -> TrainStartDecision:
    """Decide whether a ``finetune_train`` job may start GPU work.

    Manual approve is required (TC-260 / AC-FT2). Shared kill-switch and FT caps
    block start even after approve (TC-263 / AC-FT7 / TP5).
    """
    if request.kill_switch:
        return "skip_kill_switch"
    if not request.approved:
        return "skip_pending_approve"
    if request.running_count >= request.max_concurrent:
        return "skip_at_capacity"
    if request.runs_started_today >= request.max_runs_per_day:
        return "skip_daily_cap"
    return "start"


def is_finetune_auto_promote_enabled() -> bool:
    """Always false — promote is human judgment only (AC-FT4 / RD-338)."""
    return False


def decide_prod_adapter_pin(
    *,
    promoted_adapter_id: str | None,
    latest_adapter_id: str | None,
) -> str | None:
    """Return the prod adapter pin, or None for base.

    Prod ``vecinita-llm`` loads only an explicitly promoted id (TC-262 / AC-FT6).
    ``latest_adapter_id`` is ignored so candidates never auto-load on prod.
    """
    _ = latest_adapter_id
    if promoted_adapter_id is None:
        return None
    pin = promoted_adapter_id.strip()
    if not pin:
        return None
    return pin


@dataclass(frozen=True, slots=True)
class CorpusChunkText:
    """Minimal chunk surface for SFT pair construction (RD-340)."""

    chunk_id: str
    text: str
    title: str | None = None


@dataclass(frozen=True, slots=True)
class SftPair:
    """One instruction/QA SFT training example derived from a corpus chunk."""

    instruction: str
    input: str
    output: str
    source_chunk_id: str


def build_sft_pairs_from_chunks(
    chunks: Sequence[CorpusChunkText],
    *,
    instruction: str = DEFAULT_SFT_INSTRUCTION,
) -> list[SftPair]:
    """Build instruction/QA SFT pairs from chunk text (AC-FT1 / RD-340).

    Empty / whitespace-only chunks are skipped. Each kept chunk becomes one pair:
    instruction (shared), input = titled context, output = chunk body.
    """
    pairs: list[SftPair] = []
    for chunk in chunks:
        body = chunk.text.strip()
        if not body:
            continue
        title = (chunk.title or "").strip()
        context = f"Title: {title}\n\n{body}" if title else body
        pairs.append(
            SftPair(
                instruction=instruction,
                input=(
                    f"Context:\n{context}\n\nQuestion: What information does this source provide?"
                ),
                output=body,
                source_chunk_id=chunk.chunk_id,
            ),
        )
    return pairs


def parse_finetune_adapter_id() -> str | None:
    """Read promoted prod adapter pin from env (empty → base / None)."""
    raw = os.environ.get(FINETUNE_ADAPTER_ID_ENV)
    if raw is None:
        return None
    pin = raw.strip()
    if not pin:
        return None
    return pin


def parse_finetune_adapter_hash() -> str | None:
    """Read promoted adapter SHA-256 hex pin (EV-316 / AC-FT11).

    Empty → None (base-only). Non-empty must be 64 lowercase hex chars.
    """
    raw = os.environ.get(FINETUNE_ADAPTER_HASH_ENV)
    if raw is None:
        return None
    pin = raw.strip().lower()
    if not pin:
        return None
    if _SHA256_HEX_RE.fullmatch(pin) is None:
        msg = "VECINITA_FINETUNE_ADAPTER_HASH must be 64-char lowercase hex SHA-256"
        raise ValueError(msg)
    return pin


def parse_lora_resolve_mode() -> LoraResolveMode:
    """Parse LoRA resolve kill-switch (default ``post_restore`` — ADR-022 EV-316)."""
    raw = os.environ.get(LLM_LORA_RESOLVE_ENV)
    if raw is None or not raw.strip():
        return "post_restore"
    mode = raw.strip().lower()
    if mode == "post_restore":
        return "post_restore"
    if mode == "snapshot_bound":
        return "snapshot_bound"
    msg = "VECINITA_LLM_LORA_RESOLVE must be post_restore or snapshot_bound"
    raise ValueError(msg)


def decide_adapter_pin_after_promote(adapter_id: str) -> str:
    """Normalize a human-promoted adapter id for ``VECINITA_FINETUNE_ADAPTER_ID``."""
    pin = adapter_id.strip()
    if not pin:
        msg = "promote requires a non-empty adapter_id"
        raise ValueError(msg)
    return pin


def decide_adapter_pin_after_rollback() -> None:
    """Clear promoted pin → prod serves base model (TC-265 / AC-FT9)."""
    return


def parse_playground_finetune_adapter_id() -> str | None:
    """Read playground pre-promote candidate adapter id (empty → None)."""
    raw = os.environ.get(PLAYGROUND_FINETUNE_ADAPTER_ID_ENV)
    if raw is None:
        return None
    pin = raw.strip()
    if not pin:
        return None
    return pin


def decide_serve_adapter_id(*, role: ServeAdapterRole) -> str | None:
    """Resolve which adapter id (if any) the LLM serve role should load.

    Prod uses only the human-promoted pin (TC-262). Playground uses a separate
    candidate env so pre-promote eval cannot stomp prod (ADR-053).
    """
    if role == "prod":
        return decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id=None,
        )
    return parse_playground_finetune_adapter_id()


def resolve_finetune_adapter_dir(
    *,
    adapter_id: str | None,
    mount: str = ADAPTERS_MOUNT_DEFAULT,
) -> str | None:
    """Map an adapter id to ``{mount}/{adapter_id}``, or None for base."""
    if adapter_id is None:
        return None
    pin = adapter_id.strip()
    if not pin:
        return None
    root = mount.rstrip("/") or ADAPTERS_MOUNT_DEFAULT
    return f"{root}/{pin}"


def merge_lora_engine_kwargs(
    base: dict[str, object],
    *,
    adapter_dir: str | None,
) -> dict[str, object]:
    """Enable vLLM LoRA when an adapter dir is selected; otherwise return base."""
    if adapter_dir is None:
        return dict(base)
    kwargs = dict(base)
    kwargs["enable_lora"] = True
    kwargs["max_loras"] = 1
    kwargs["max_lora_rank"] = DEFAULT_LORA_MAX_RANK
    return kwargs


def sha256_adapter_dir(adapter_dir: Path | str) -> str:
    """Return lowercase hex SHA-256 of a canonical adapter-directory digest (EV-316).

    For each file under ``adapter_dir`` (sorted by relative POSIX path), fold
    ``path ‖ NUL ‖ size ‖ NUL ‖ bytes`` into an outer SHA-256. Symlinks that escape
    the adapter root raise ``ValueError``.
    """
    root = Path(adapter_dir).resolve()
    if not root.is_dir():
        msg = f"adapter directory missing: {root}"
        raise RuntimeError(msg)

    outer = hashlib.sha256()
    entries: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            target = path.resolve()
            try:
                _ = target.relative_to(root)
            except ValueError as exc:
                msg = f"adapter symlink escapes root: {path}"
                raise ValueError(msg) from exc
            if target.is_file():
                entries.append((path.relative_to(root).as_posix(), target))
            continue
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(), path))

    for rel, file_path in entries:
        data = file_path.read_bytes()
        outer.update(rel.encode("utf-8"))
        outer.update(b"\0")
        outer.update(str(len(data)).encode("ascii"))
        outer.update(b"\0")
        outer.update(data)
    return outer.hexdigest()


def verify_adapter_integrity(
    *,
    adapter_dir: Path | str,
    expected_hash: str,
) -> str:
    """Fail closed unless directory digest matches expected SHA-256 (AC-FT11).

    Returns the computed digest when it matches (constant-time compare).
    """
    root = Path(adapter_dir)
    if not root.is_dir():
        msg = f"promoted LoRA adapter missing on volume: {root}"
        raise RuntimeError(msg)
    expected = expected_hash.strip().lower()
    if _SHA256_HEX_RE.fullmatch(expected) is None:
        msg = "expected adapter hash must be 64-char lowercase hex SHA-256"
        raise ValueError(msg)
    actual = sha256_adapter_dir(root)
    if not hmac.compare_digest(actual, expected):
        msg = (
            f"LoRA adapter hash mismatch: expected {expected[:12]}… "
            f"got {actual[:12]}… (fail closed)"
        )
        raise RuntimeError(msg)
    return actual


def build_prod_llm_health(
    *,
    base_model_id: str,
    adapter_id: str | None,
    adapter_hash: str | None,
    git_commit: str | None,
    snapshot_schema: str = LLM_SNAPSHOT_SCHEMA,
) -> dict[str, str | None]:
    """Build prod ``GET /health`` ready metadata (TC-316-02 / ADR-022 EV-316)."""
    return {
        "status": "ok",
        "base_model_id": base_model_id,
        "adapter_id": adapter_id,
        "adapter_hash": adapter_hash,
        "snapshot_schema": snapshot_schema,
        "git_commit": git_commit,
    }


def require_post_restore_adapter_hash(*, adapter_id: str | None) -> str | None:
    """When post_restore and an adapter is pinned, require a hash env (fail closed)."""
    if adapter_id is None:
        return None
    expected = parse_finetune_adapter_hash()
    if expected is None:
        msg = (
            "VECINITA_FINETUNE_ADAPTER_HASH is required when "
            "VECINITA_FINETUNE_ADAPTER_ID is set (post_restore)"
        )
        raise RuntimeError(msg)
    return expected

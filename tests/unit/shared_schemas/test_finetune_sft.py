"""T129.2 — F77 SFT pair builder from chunks + adapter pin/clear rollback.

[Corpus: feature-list.md §F77]
[Spec: docs/acceptance-criteria.md §AC-FT1 §AC-FT9]
[Spec: docs/test-plan.md §TC-265]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/decisions.md §RD-340]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_ADAPTER_ID]
"""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.finetune import (
    DEFAULT_SFT_INSTRUCTION,
    CorpusChunkText,
    build_sft_pairs_from_chunks,
    decide_adapter_pin_after_promote,
    decide_adapter_pin_after_rollback,
    decide_prod_adapter_pin,
    parse_finetune_adapter_id,
)


def test_build_sft_pairs_from_chunks_skips_empty_and_keeps_body() -> None:
    """RD-340 / AC-FT1: instruction/QA pairs from non-empty chunk text."""
    chunks = [
        CorpusChunkText(chunk_id="c1", text="  ", title="Ignored"),
        CorpusChunkText(
            chunk_id="c2",
            text="ESL classes meet Mondays.",
            title="Providence ESL",
        ),
        CorpusChunkText(chunk_id="c3", text="Food pantry hours.", title=None),
    ]

    pairs = build_sft_pairs_from_chunks(chunks)

    expected_pairs = 2
    assert len(pairs) == expected_pairs
    assert pairs[0].source_chunk_id == "c2"
    assert pairs[0].instruction == DEFAULT_SFT_INSTRUCTION
    assert "Providence ESL" in pairs[0].input
    assert pairs[0].output == "ESL classes meet Mondays."
    assert pairs[1].source_chunk_id == "c3"
    assert "Title:" not in pairs[1].input
    assert pairs[1].output == "Food pantry hours."


def test_build_sft_pairs_custom_instruction() -> None:
    """Optional instruction override is applied to every pair."""
    custom = "Reply briefly using only the context."
    pairs = build_sft_pairs_from_chunks(
        [CorpusChunkText(chunk_id="c1", text="Hello")],
        instruction=custom,
    )
    expected_one = 1
    assert len(pairs) == expected_one
    assert pairs[0].instruction == custom


def test_build_sft_pairs_empty_corpus_returns_empty() -> None:
    """No usable chunks → empty SFT set (train should not invent pairs)."""
    assert build_sft_pairs_from_chunks([]) == []
    assert (
        build_sft_pairs_from_chunks(
            [CorpusChunkText(chunk_id="c1", text="\n\t")],
        )
        == []
    )


def test_promote_then_rollback_clears_prod_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-265 / AC-FT9: promote sets pin; rollback clears → base."""
    promoted = decide_adapter_pin_after_promote("  adapter-v3  ")
    assert promoted == "adapter-v3"
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", promoted)
    assert parse_finetune_adapter_id() == "adapter-v3"
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id="adapter-latest",
        )
        == "adapter-v3"
    )

    cleared = decide_adapter_pin_after_rollback()
    assert cleared is None
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "")
    assert parse_finetune_adapter_id() is None
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=cleared,
            latest_adapter_id="adapter-latest",
        )
        is None
    )


def test_promote_rejects_empty_adapter_id() -> None:
    """Human promote requires a non-empty adapter id."""
    with pytest.raises(ValueError, match="non-empty"):
        decide_adapter_pin_after_promote("   ")


def test_parse_finetune_adapter_id_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset pin env → base (None)."""
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_ID", raising=False)
    assert parse_finetune_adapter_id() is None

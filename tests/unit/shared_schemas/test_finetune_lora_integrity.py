"""TC-316 — LoRA post-restore SHA-256 integrity + ready metadata (EV-316 / #316).

[Corpus: feature-list.md §F80]
[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-316]
[Spec: docs/test-plan.md §TC-316-01 §TC-316-02]
[Spec: docs/acceptance-criteria.md §AC-FT11]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_ADAPTER_HASH §VECINITA_LLM_LORA_RESOLVE]
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import pytest
from vecinita_shared_schemas.finetune import (
    LLM_SNAPSHOT_SCHEMA,
    build_prod_llm_health,
    parse_finetune_adapter_hash,
    parse_lora_resolve_mode,
    parse_playground_finetune_adapter_id,
    require_post_restore_adapter_hash,
    resolve_finetune_adapter_dir,
    sha256_adapter_dir,
    verify_adapter_integrity,
)

_SHA256_HEX_LEN = 64


def _write_adapter(root: Path, *, name: str, files: dict[str, bytes]) -> Path:
    adapter = root / name
    adapter.mkdir(parents=True)
    for rel, body in files.items():
        path = adapter / rel
        _ = path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_bytes(body)
    return adapter


def test_sha256_adapter_dir_is_stable_and_cryptographic(tmp_path: Path) -> None:
    """TC-316-01: canonical SHA-256 digest (not MD5/CRC); order-independent paths."""
    adapter = _write_adapter(
        tmp_path,
        name="adapter-a",
        files={"adapter_config.json": b'{"r":8}', "weights.bin": b"\x00\x01\x02"},
    )
    digest = sha256_adapter_dir(adapter)
    assert len(digest) == _SHA256_HEX_LEN
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)
    outer = hashlib.sha256()
    for rel in ("adapter_config.json", "weights.bin"):
        data = (adapter / rel).read_bytes()
        outer.update(rel.encode("utf-8"))
        outer.update(b"\0")
        outer.update(str(len(data)).encode("ascii"))
        outer.update(b"\0")
        outer.update(data)
    assert digest == outer.hexdigest()
    assert digest == sha256_adapter_dir(adapter)


def test_sha256_rejects_symlink_escape(tmp_path: Path) -> None:
    """Symlink that escapes the adapter root must fail closed."""
    outside = tmp_path / "secret.bin"
    _ = outside.write_bytes(b"leak")
    adapter = tmp_path / "adapter-a"
    adapter.mkdir()
    _ = (adapter / "ok.txt").write_bytes(b"ok")
    _ = (adapter / "escape").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        _ = sha256_adapter_dir(adapter)


def test_verify_adapter_integrity_fail_closed_on_mutate(tmp_path: Path) -> None:
    """TC-316-01: promote A → mutate volume → must not accept A's hash for B content."""
    adapter = _write_adapter(
        tmp_path,
        name="adapter-a",
        files={"w.bin": b"AAAA"},
    )
    hash_a = sha256_adapter_dir(adapter)
    _ = verify_adapter_integrity(adapter_dir=adapter, expected_hash=hash_a)

    _ = (adapter / "w.bin").write_bytes(b"BBBB")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        _ = verify_adapter_integrity(adapter_dir=adapter, expected_hash=hash_a)

    hash_b = sha256_adapter_dir(adapter)
    assert not hmac.compare_digest(hash_a, hash_b)
    _ = verify_adapter_integrity(adapter_dir=adapter, expected_hash=hash_b)


def test_verify_missing_dir_fail_closed(tmp_path: Path) -> None:
    """Missing adapter directory fails closed (AC-FT11)."""
    missing = tmp_path / "nope"
    with pytest.raises(RuntimeError, match="missing"):
        _ = verify_adapter_integrity(adapter_dir=missing, expected_hash="a" * _SHA256_HEX_LEN)


def test_parse_finetune_adapter_hash_and_resolve_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-316-02: hash env + default post_restore kill-switch."""
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_HASH", raising=False)
    assert parse_finetune_adapter_hash() is None

    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_HASH", "  " + ("ab" * 32) + "  ")
    assert parse_finetune_adapter_hash() == "ab" * 32

    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_HASH", "not-hex")
    with pytest.raises(ValueError, match="SHA-256"):
        _ = parse_finetune_adapter_hash()

    monkeypatch.delenv("VECINITA_LLM_LORA_RESOLVE", raising=False)
    assert parse_lora_resolve_mode() == "post_restore"
    monkeypatch.setenv("VECINITA_LLM_LORA_RESOLVE", "snapshot_bound")
    assert parse_lora_resolve_mode() == "snapshot_bound"
    monkeypatch.setenv("VECINITA_LLM_LORA_RESOLVE", "weird")
    with pytest.raises(ValueError, match="post_restore"):
        _ = parse_lora_resolve_mode()


def test_build_prod_llm_health_ready_metadata() -> None:
    """TC-316-02: /health contract fields."""
    payload = build_prod_llm_health(
        base_model_id="qwen2.5:1.5b-instruct",
        adapter_id="adapter-a",
        adapter_hash="a" * _SHA256_HEX_LEN,
        git_commit="abc1234",
    )
    assert payload == {
        "status": "ok",
        "base_model_id": "qwen2.5:1.5b-instruct",
        "adapter_id": "adapter-a",
        "adapter_hash": "a" * _SHA256_HEX_LEN,
        "snapshot_schema": LLM_SNAPSHOT_SCHEMA,
        "git_commit": "abc1234",
    }
    assert LLM_SNAPSHOT_SCHEMA == "v1"
    base = build_prod_llm_health(
        base_model_id="qwen2.5:1.5b-instruct",
        adapter_id=None,
        adapter_hash=None,
        git_commit=None,
    )
    assert base["adapter_id"] is None
    assert base["adapter_hash"] is None
    assert base["git_commit"] is None


def test_llm_app_health_uses_ready_metadata_builder() -> None:
    """Prod ASGI health wires build_prod_llm_health / _prod_health_payload."""
    source = (Path(__file__).resolve().parents[3] / "infra" / "modal" / "llm_app.py").read_text(
        encoding="utf-8"
    )
    assert "_prod_health_payload" in source
    assert "build_prod_llm_health" in source


def test_parse_hash_empty_string_and_explicit_post_restore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only hash → None; explicit post_restore mode accepted."""
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_HASH", "   ")
    assert parse_finetune_adapter_hash() is None
    monkeypatch.setenv("VECINITA_LLM_LORA_RESOLVE", "post_restore")
    assert parse_lora_resolve_mode() == "post_restore"


def test_sha256_adapter_dir_missing_raises(tmp_path: Path) -> None:
    """sha256_adapter_dir fail-closed when path is not a directory."""
    with pytest.raises(RuntimeError, match="missing"):
        _ = sha256_adapter_dir(tmp_path / "absent")


def test_sha256_skips_in_tree_symlink_to_directory(tmp_path: Path) -> None:
    """In-tree symlink to a directory is skipped (only files contribute)."""
    adapter = tmp_path / "adapter-a"
    nested = adapter / "subdir"
    nested.mkdir(parents=True)
    _ = (adapter / "w.bin").write_bytes(b"x")
    _ = (adapter / "link-dir").symlink_to(nested)
    digest = sha256_adapter_dir(adapter)
    assert len(digest) == _SHA256_HEX_LEN


def test_verify_rejects_malformed_expected_hash(tmp_path: Path) -> None:
    """Expected hash must be 64-char hex before compare."""
    adapter = _write_adapter(tmp_path, name="adapter-a", files={"w.bin": b"x"})
    with pytest.raises(ValueError, match="64-char"):
        _ = verify_adapter_integrity(adapter_dir=adapter, expected_hash="deadbeef")


def test_require_post_restore_adapter_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pinned adapter requires HASH env; base pin does not."""
    assert require_post_restore_adapter_hash(adapter_id=None) is None
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_HASH", raising=False)
    with pytest.raises(RuntimeError, match="ADAPTER_HASH is required"):
        _ = require_post_restore_adapter_hash(adapter_id="adapter-a")
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_HASH", "ab" * 32)
    assert require_post_restore_adapter_hash(adapter_id="adapter-a") == "ab" * 32


def test_playground_and_resolve_empty_pin_edge_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty playground pin and whitespace adapter id resolve to None."""
    monkeypatch.setenv("VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID", "   ")
    assert parse_playground_finetune_adapter_id() is None
    assert resolve_finetune_adapter_dir(adapter_id="   ") is None


def test_sha256_skips_symlink_to_non_file(tmp_path: Path) -> None:
    """In-tree symlink whose target is not a regular file is skipped."""
    adapter = tmp_path / "adapter-a"
    adapter.mkdir()
    _ = (adapter / "w.bin").write_bytes(b"x")
    _ = (adapter / "self-link").symlink_to(adapter)
    digest = sha256_adapter_dir(adapter)
    assert len(digest) == _SHA256_HEX_LEN

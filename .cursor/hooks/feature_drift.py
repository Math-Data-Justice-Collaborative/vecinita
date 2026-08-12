"""Cursor afterFileEdit hook: maps edited files to their feature/component for context.

Advisory only — provides context about which approved feature the edit belongs to.
Never blocks — always exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

FILE_FEATURE_MAP: list[tuple[str, str]] = [
    # EV-027 — more specific prefixes first
    (
        "infra/modal/finetune",
        "F77: Modal LoRA FT (ADR-053) — train/approve; not antibody src/finetune",
    ),
    (
        "infra/modal/llm_app.py",
        "ADR-037 / F77: prod vecinita-llm — load adapter only after human promote",
    ),
    (
        "infra/modal/llm_playground_app.py",
        "ADR-037 / F77: playground may load candidate adapters pre-promote",
    ),
    (
        "infra/modal/data_management_app.py",
        "F75/F76: DM Modal — catch-up + freshness schedule / job types",
    ),
    ("infra/modal/embedding_app.py", "Modal FastEmbed service"),
    ("infra/modal/", "Modal services (llm / embed / DM / FT)"),
    ("apps/data-management", "F75–F77: Admin DM UI + jobs (automations / freshness / FT)"),
    ("apps/internal-write-api", "F75–F77: write-API — automation_runs, promote, corpus"),
    ("apps/chat-rag", "ChatRAG — prod inference (adapter pin after F77 promote)"),
    ("packages/ingest/", "F75/F76: ingest — catch-up embed path + freshness re-fetch"),
    ("packages/llm-client/", "ADR-037: unified LLM client"),
    ("packages/rag/", "RAG retrieve/pack"),
    ("packages/embedding-client/", "Embedding client"),
    ("packages/shared-schemas/", "Shared schemas"),
    ("tests/e2e/test_uj080", "F75: UJ-080 automations e2e"),
    ("tests/e2e/test_uj081", "F76: UJ-081 freshness e2e"),
    ("tests/e2e/test_uj082", "F77: UJ-082 FT approve/promote e2e"),
    # Legacy antibody template
    ("src/app.py", "Modal App — entry point (ADR-001), GPU class variants, @modal.enter()"),
    ("src/pipeline.py", "F5: Pipeline Orchestrator — chains F1→F2→F3, manages intermediates"),
    ("src/weights.py", "F6: Weight Manager — download, SHA256 verify, Modal Volume cache"),
    ("src/config.py", "F5/F7: Config Module — parsing, validation, defaults"),
    ("src/output.py", "F5: Output Packaging — ZIP, results.json"),
    ("src/rfdiffusion_stage.py", "F1: RFdiffusion — CDR backbone generation (ADR-002: flat module)"),
    ("src/proteinmpnn_stage.py", "F2: ProteinMPNN — sequence design (ADR-002: flat module)"),
    ("src/rf2_stage.py", "F3/F4: RF2 — in-silico validation + TCR-MHC mode (ADR-002: flat module)"),
    ("src/finetune/", "F8 antibody Fine-Tuning — NOT F77 LoRA (use infra/modal FT)"),
    ("tests/", "Test Suite — see docs/test-plan.md for test case definitions"),
    ("docs/", "Documentation — spec-driven, see docs/ for all specs"),
]


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def match_feature(rel_path: str) -> str | None:
    posix = str(PurePosixPath(rel_path))
    for prefix, feature in FILE_FEATURE_MAP:
        if posix == prefix.rstrip("/") or posix.startswith(prefix):
            return feature
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    raw = payload.get("filePath") or payload.get("file_path") or ""
    if not raw:
        print("{}")
        return 0

    file_path = Path(raw)
    if file_path.suffix != ".py":
        print("{}")
        return 0

    repo = find_repo_root(file_path)
    if repo is None:
        print("{}")
        return 0

    try:
        rel = file_path.resolve().relative_to(repo.resolve())
    except ValueError:
        print("{}")
        return 0

    rel_str = str(rel).replace("\\", "/")
    feature = match_feature(rel_str)

    if feature:
        result = {"additional_context": f"[feature-context] {feature}"}
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

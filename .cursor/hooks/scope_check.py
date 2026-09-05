"""Cursor preToolUse hook: advisory check that new files map to approved components.

Reads the file path from stdin JSON, checks against the component list in docs/spec.md,
and returns advisory context. Never blocks — always exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

APPROVED_COMPONENTS: dict[str, str] = {
    # Vecinita monorepo (EV-027 F75–F77 and standing apps) — check before legacy prefixes
    "infra/modal/finetune": "F77 Modal LoRA FT app (ADR-053)",
    "infra/modal/llm_app.py": "Modal vecinita-llm (ADR-037; F77 adapter load after promote)",
    "infra/modal/llm_playground_app.py": "Modal vecinita-llm-playground (ADR-037)",
    "infra/modal/data_management_app.py": "Modal DM workers (F75/F76 automations + jobs)",
    "infra/modal/embedding_app.py": "Modal FastEmbed",
    "infra/modal/rerank_app.py": "Modal vecinita-rerank CE (F45 / EV-029)",
    "infra/modal": "Modal services (llm / embed / DM / FT)",
    "apps/data-management": "Data Management backend/FE (F75–F77 UI + jobs)",
    "apps/internal-write-api": "Internal write API (automation_runs, promote, corpus)",
    "apps/chat-rag": "ChatRAG backend/FE",
    "apps/database": "Alembic / schema",
    "packages/ingest": "Ingest pipeline (F76 freshness / F75 catch-up)",
    "packages/llm-client": "LLM client (ADR-037)",
    "packages/rag": "RAG retrieve/pack",
    "packages/embedding-client": "Embedding client",
    "packages/shared-schemas": "Shared schemas / OpenAPI models",
    "packages": "Shared packages",
    "apps": "DO apps",
    "infra": "Infra (Modal / DO / compose)",
    "openapi": "OpenAPI contracts",
    "scripts": "Ops / CI scripts",
    # Legacy template (antibody job) — retain for any residual src/
    "src/app.py": "Modal App (F5/F6/F8/F9) — legacy template",
    "src/pipeline.py": "Pipeline Orchestrator (F5) — legacy template",
    "src/weights.py": "Weight Manager (F6) — legacy template",
    "src/config.py": "Config Module (F5/F7) — legacy template",
    "src/output.py": "Output Packaging (F5) — legacy template",
    "src/rfdiffusion_stage.py": "RFdiffusion Stage (F1) — legacy template",
    "src/proteinmpnn_stage.py": "ProteinMPNN Stage (F2) — legacy template",
    "src/rf2_stage.py": "TCR RF2 Stage (F4 only, ADR-007) — legacy template",
    "src/finetune": "Antibody Fine-Tune Module (F8) — NOT F77 LoRA; use infra/modal FT",
    "tests": "Test Suite",
    "docs": "Documentation",
    ".cursor": "Cursor Tooling",
    ".github": "CI/CD",
}


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def match_component(rel_path: str) -> str | None:
    posix = PurePosixPath(rel_path)
    path_str = str(posix)
    for prefix, component in APPROVED_COMPONENTS.items():
        if path_str == prefix or path_str.startswith(prefix + "/"):
            return component
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
    component = match_component(rel_str)

    if component:
        result = {"additional_context": f"[scope-check] File maps to: {component}"}
    else:
        result = {
            "additional_context": (
                f"[scope-check] WARNING: '{rel_str}' does not map to any approved "
                "component (docs/spec.md / F75–F77 surfaces). Verify scope or raise "
                "[Scope Drift]."
            )
        }

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

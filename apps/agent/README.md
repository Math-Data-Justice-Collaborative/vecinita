# Vecinita agent (FastAPI)

Canonical **agent application code** lives in `src/agent/` (import path `src.agent`).

The **gateway** tree (`../gateway/`) still owns shared modules (`src.config`, `src.services.modal`, `src.embedding_service`, etc.), tests, `pyproject.toml`, and `uv.lock`. The gateway image copies `../gateway/src/`; the **agent** image uses the same tree via repo-root `dockerContext: .` (see `Dockerfile`).

`../gateway/src/agent` is a **symlink** to this directory’s `src/agent` so local tooling and Docker builds share one logical `src` package. Prefer editing files under **`apis/agent/src/agent/`** for agent-only changes.

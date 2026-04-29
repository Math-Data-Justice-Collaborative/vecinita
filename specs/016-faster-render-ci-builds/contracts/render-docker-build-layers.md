# Contract: Render Docker build layering

**Feature**: [spec.md](../spec.md)  
**Purpose**: Speed **code-only** deploys (**FR-003**) via **cache-friendly** image layers without changing runtime behavior.

## Requirements

1. **Copy order**: Install **system packages** and **application dependencies** in layers **before** copying the full application source tree, so unrelated code edits reuse cached dependency layers.

2. **Context**: `dockerContext` in `render.yaml` MUST stay minimal; maintain **`.dockerignore`** next to the Dockerfile to exclude `tests/`, `htmlcov/`, `.git`, and other non-runtime paths unless explicitly required for build.

3. **Multi-service reuse**: Gateway, agent, and other services sharing `backend/Dockerfile` MUST rely on **build-args** or identical stages only if **image digest** or tag strategy does not confuse rollback; document any **TARGET** stage name in this file when introduced.

4. **No functional change**: Base image OS and Python/Node major versions MUST NOT change in the same PR as layer reordering unless treated as a **dependency_lock** / image-change category with its own baseline (**spec** edge cases).

## Verification

- Compare Render **build** duration for two deploys: (A) lockfile-only change, (B) single-file Python change — expect (B) to benefit from layer cache after (A) warmed the stack.

## Audit vs `backend/Dockerfile` (2026-04-28, T003)

Observed layout: **builder** stage installs OS build deps, copies **`pyproject.toml`**, runs **`pip install`** to `/install` with a **pinned explicit package list** (not `pip install .` from lockfile); **runtime** stage copies `/install` then **`COPY src/`** and **`COPY scripts/`**. **COPY order** already keeps dependency layers **before** application source, which satisfies requirement **1** for this Dockerfile.

Gaps / follow-ups (document only; behavior unchanged in T003):

- **Lockfile / manifest alignment**: **`backend/Dockerfile`** now **`COPY pyproject.toml uv.lock`** before **`pip install`** so the dependency layer invalidates when the lockfile changes; installs remain the **curated pip list** (not a full `uv export`) to preserve the small Render image — unifying install with **`uv.lock`** is a follow-up if memory budget allows.
- **`.dockerignore`**: **`backend/.dockerignore`** added (**T013**) — see that file for `**/*.md` / `!src/**/*.md` rationale (runtime rules under `src/` must stay in context).
- **`dockerContext`**: root **`render.yaml`** uses minimal contexts per service (**T014** snapshot in governance artifact). **`apps/data-management-frontend/render.yaml`** still references **`./apps/frontend/`**, which is not the current monorepo layout — treat as stale; align in a dedicated change, not silently here.

**Last reviewed**: 2026-04-28 (US2 T012–T014)

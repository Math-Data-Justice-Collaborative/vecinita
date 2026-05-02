# Contract: Modal HTTP ban (FR-001) and SC-005 enforcement

**Feature**: [015-openapi-sdk-clients](../spec.md)  
**Clarification**: Session 2026-04-24 — **Option B** strict (no HTTP(S) to Modal-assigned hostnames from **any** checked-in code).

## Normative rules

1. **Forbidden**: Any HTTP client library call (`httpx`, `requests`, `urllib.request`, `fetch`, Axios, etc.) whose **request URL host** matches a **blocked pattern** (below), in **any** file under version control—including `modal-apps/scraper/` Modal app sources.

2. **Allowed**: **Modal SDK** usage (`modal.Function.from_name`, `.remote()`, `.spawn`, `.map`, `@app.function`, etc.) for reaching Modal-hosted compute.

3. **Allowed**: HTTP(S) to **Render** gateway, agent, data-management, or other **non-Modal** hosts using **generated OpenAPI clients** and **FR-004** env bases.

## Blocked host patterns (minimum set)

Maintain in-repo list at **`config/modal_http_ban_patterns.txt`** (one literal fragment per line; see file header). Optional **`config/modal_http_ban_allowlist_paths.txt`** lists repo-relative files where **URL-only** `https?://…` matches are suppressed until legacy OpenAPI examples and config strings are migrated (**not** an exemption for real `httpx` / `requests` calls to Modal).

| Pattern | Rationale |
|---------|-----------|
| `modal.run` | Common Modal deployment host suffix |
| `modal.com` | Only if used as HTTP API host in practice—**tasks** confirm via `rg` inventory before adding |

**Updates**: Any new Modal TLD or hostname class used by the workspace MUST be added here **before** merge if HTTP to it would violate FR-001.

## Exclusions (SC-001 / SC-005 quarantine)

- `node_modules/`, `.venv/`, `venv/`, `dist/`, build caches
- **Lockfiles** and minified third-party bundles (no hand-editing)
- **Committed upstream vendored** trees—**must remain empty**; do not vendor Modal HTTP clients to bypass ban

## Implementation shapes (pick in tasks)

| Approach | Pros | Cons |
|----------|------|------|
| `rg`-based gate in `make check-modal-http` | Fast, simple | False positives on strings in docs—use path filters + allowlist |
| Python AST walker | Fewer false positives | More code to maintain |
| Pre-commit hook | Early feedback | Duplicates CI if not everyone installs hooks |

**Recommendation**: **`make check-modal-http`** invoking a small Python script that shells `rg` with `--glob` negations matching exclusions, plus optional AST pass for string literals passed to **`httpx`**, **`requests`**, **`urllib.request`**, and (where feasible) **`fetch`** / **`axios`** calls so coverage matches **FR-001** in [spec.md](../spec.md).

## Evidence for reviewers

- PR template checkbox: “`make check-modal-http` green”
- Link to this contract from `RENDER_SHARED_ENV_CONTRACT.md` after implementation.

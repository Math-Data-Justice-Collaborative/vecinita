# Typing policy — no `Any` / `any`

> **Status:** Enforced in CI and Cursor hooks (ADR-018, EV-003)  
> **Last updated:** 2026-05-27

Vecinita requires **strict static typing**. Do not use `typing.Any` in Python or `any` in TypeScript except where an external boundary cannot be typed and a documented waiver exists (none today).

## Quick reference

| Check | Command |
|-------|---------|
| Python lint (includes `ANN401`) | `uv run ruff check apps packages tests` |
| Python types | `uv run basedpyright apps packages tests` |
| ChatRAG frontend | `cd apps/chat-rag-frontend && npm run lint && npm run build` |
| Data-mgmt frontend | `cd apps/data-management-frontend && npm run lint && npm run build` |

## Python

### Ruff

- Rule **`ANN401`**: `typing.Any` is disallowed in annotations (function args, returns, variables).
- Config: `[tool.ruff.lint]` → `select` includes `ANN401` in root `pyproject.toml`.

### basedpyright

- Package: **`basedpyright`** (Pyright-compatible; adds `reportExplicitAny`).
- Config sections: `[tool.basedpyright]` in `pyproject.toml` and `pyrightconfig.json`.
- Key settings:
  - **`reportExplicitAny = "error"`** — rejects `dict[str, Any]`, `payload: Any`, etc.
  - **`reportAny = "error"`** — rejects *using* values typed as `Any` (e.g. untyped SQLAlchemy scalars). Use `db_mapping` / `json_types` helpers.
- Excludes: `**/node_modules` under `apps/` (frontend vendored Python).

### Alternatives to `Any`

| Use case | Prefer |
|----------|--------|
| Arbitrary JSON object | `JsonObject` / `JsonValue` from `vecinita_shared_schemas.json_types` |
| Request body before validation | `Mapping[str, object]` → `validate_ask_request()` |
| Structured job persistence | `TypedDict` (e.g. `JobPayload` in data-management store) |
| SQLAlchemy connection | `sqlalchemy.engine.Connection` |
| IDs | `uuid.UUID` |
| Logging extras | `**extra: str \| int \| float \| bool \| None` |

## TypeScript

### ESLint (both `*-frontend` apps)

Type-aware lint (`parserOptions.projectService: true`):

Production `src/**` uses **`typescript-eslint` `strictTypeChecked`** (includes `no-explicit-any` and strict inference rules). Test files (`src/test/**`) keep `no-explicit-any` but relax mock-noisy rules (`require-await`, etc.).

Config: `apps/*/eslint.config.js`.

### TypeScript compiler

`tsconfig.json` per frontend:

- `"strict": true`
- `"noImplicitAny": true`

`npm run build` runs `tsc --noEmit` before Vite.

### Test mocks

Type Vitest mocks explicitly:

```typescript
const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>();
```

Avoid `expect.objectContaining` for headers when it triggers `no-unsafe-assignment`; assert `fetchMock.mock.calls[0]?.[1]` with `Headers` instead.

## Waivers

- Pyright/basedpyright: use `# pyright: ignore[rule]` with a **specific rule code** only when unavoidable.
- ESLint: `eslint-disable-next-line @typescript-eslint/<rule>` with justification in PR.
- New waivers require updating this doc or an ADR amendment.

## Helpers (Python)

| Module | Use |
|--------|-----|
| `vecinita_shared_schemas.db_mapping` | SQLAlchemy rows/scalars (`mapping_row`, `row_uuid`, `sqlalchemy_scalar_one`, …) |
| `vecinita_shared_schemas.json_types` | JSON (`JsonObject`, `as_json_object`) |
| `tests/helpers/json_response.py` | Typed `TestClient` / httpx JSON in tests |

## Traceability

- ADR: [ADR-018](adr/ADR-018-strict-typing-no-any.md)
- CI: `.github/workflows/ci.yml`
- Cursor: `.cursor/rules/strict-typing.mdc`, `.cursor/hooks/typecheck.py`

# Typing policy — no `Any` / `any`

> **Status:** Enforced in CI and Cursor hooks (ADR-018, EV-003)  
> **Last updated:** 2026-06-29

Vecinita requires **strict static typing**. Do not use `typing.Any` in Python or `any` in TypeScript except where an external boundary cannot be typed and a documented waiver exists (none today).

As of 2026-06-29 the linters/typecheckers run at their strictest sensible settings: Ruff
`select = ["ALL"]`, basedpyright `typeCheckingMode = "strict"`, and all strict TypeScript
compiler flags. See the per-stack sections below for the exact config and the small set of
deliberately-ignored rules (formatter conflicts and mutually-incompatible rule pairs).

## Quick reference

| Check | Command |
|-------|---------|
| Python lint (includes `ANN401`) | `uv run ruff check apps packages tests` |
| Python types | `uv run basedpyright apps packages tests` |
| ChatRAG frontend | `cd apps/chat-rag-frontend && npm run lint && npm run build` |
| Data-mgmt frontend | `cd apps/data-management-frontend && npm run lint && npm run build` |

## Python

### Ruff

- **`select = ["ALL"]`** — every Ruff rule family is enabled (the strictest setting),
  including `ANN` (annotations, so `typing.Any` is still rejected via `ANN401`), `D`
  (docstrings, google convention), `S` (security), `PL` (pylint), `TRY`, `EM`, `PT`, etc.
- Config: `[tool.ruff.lint]` in root `pyproject.toml`.
- **Deliberate `ignore` list** (only rules that conflict with our formatter or each other):
  | Rule | Why ignored |
  |------|-------------|
  | `E501` | `ruff format` owns line wrapping |
  | `COM812` | Conflicts with `ruff format` (Ruff officially recommends disabling) |
  | `ISC001` | Conflicts with `ruff format` |
  | `D203` | Mutually incompatible with `D211` (we keep `D211`) |
  | `D213` | Mutually incompatible with `D212` (we keep `D212`) |
- **Per-file ignores**: `tests/**` ignores **only** `S101` — `assert` is the foundation of
  pytest; everything else (docstrings, annotations, magic-value constants, etc.) is enforced
  in tests at the same strictness as production code.
- `[tool.ruff.lint.pydocstyle] convention = "google"`.

### basedpyright

- Package: **`basedpyright`** (Pyright-compatible; adds `reportExplicitAny`).
- Config sections: `[tool.basedpyright]` in `pyproject.toml` and `pyrightconfig.json`.
- Key settings:
  - **`typeCheckingMode = "strict"`** — Pyright strict mode (the strongest sensible level;
    `all` adds non-type stylistic rules like `reportUnusedCallResult` that cannot be resolved
    by adding types). Strict requires complete type information everywhere.
  - **`reportExplicitAny = "error"`** — rejects `dict[str, Any]`, `payload: Any`, etc.
  - **`reportAny = "error"`** — rejects *using* values typed as `Any` (e.g. untyped SQLAlchemy scalars). Use `db_mapping` / `json_types` helpers.
  - **`stubPath = "stubs"`** — local `.pyi` stubs for genuinely untyped third-party libs.
- Untyped third-party libraries (e.g. LlamaIndex): resolve `reportUnknown*` by annotating the
  call site, `cast(...)`, repo helpers (`db_mapping` / `json_types`), or local stubs under
  `stubs/`. A targeted `# pyright: ignore[specificCode]  # reason` is a last resort only.
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

`tsconfig.json` per frontend app **and** shared `packages/frontend-*`:

- `"strict": true`, `"noImplicitAny": true`
- `"noUnusedLocals"`, `"noUnusedParameters"`, `"noFallthroughCasesInSwitch"`,
  `"noUncheckedSideEffectImports"`
- **Added (strictest sensible set):** `"noUncheckedIndexedAccess"`,
  `"exactOptionalPropertyTypes"`, `"noImplicitReturns"`, `"noImplicitOverride"`,
  `"noPropertyAccessFromIndexSignature"`, `"verbatimModuleSyntax"`,
  `"allowUnreachableCode": false`, `"allowUnusedLabels": false`,
  `"forceConsistentCasingInFileNames"`

Notes on the strict flags:
- `exactOptionalPropertyTypes`: option-bag types that intentionally carry `undefined` declare
  the property as `prop?: T | undefined` (the documented pattern), rather than omitting it.
- `noPropertyAccessFromIndexSignature`: read index-signature properties with bracket access
  (`obj["key"]`), including header maps and `Record<string, unknown>` type guards.
- `verbatimModuleSyntax`: type-only imports must use `import { type X }` / `import type`.

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

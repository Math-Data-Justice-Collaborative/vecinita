# ADR-018: Strict static typing — no `Any` / `any`

**Status:** Accepted  
**Date:** 2026-05-27  
**Cycle:** EV-003  
**Deciders:** Engineering (evolve request)

## Context

Vecinita uses Python 3.11 (backends, packages) and TypeScript (React/Vite frontends). Loose typing (`typing.Any`, explicit `any`, unsafe flows from untyped values) hides bugs until runtime and conflicts with spec-driven, test-backed delivery.

Upstream Pyright does not ban explicit `Any` ([pyright#6165](https://github.com/microsoft/pyright/issues/6165)). **basedpyright** adds `reportExplicitAny`.

## Decision

Enforce a **no-Any / no-any** policy in CI, Cursor hooks, and local dev:

| Language | Linter | Typechecker / compiler |
|----------|--------|-------------------------|
| Python | Ruff **`ANN401`** (no `typing.Any` in annotations) | **basedpyright** `reportExplicitAny` + **`reportAny`** = error |
| TypeScript | ESLint **`strictTypeChecked`** on `src/**` (excludes `src/test/**`) | `tsconfig` **`strict`** + **`noImplicitAny`** |

Canonical reference: [`docs/typing-policy.md`](../typing-policy.md).

### Python details

- Dev dependency: **`basedpyright`** (replaces standalone `pyright` in CI and hooks).
- Config: `[tool.basedpyright]` in `pyproject.toml` and `pyrightconfig.json` (IDE parity).
- JSON-shaped blobs: use `vecinita_shared_schemas.json_types.JsonObject` / `JsonValue` or `Mapping[str, object]` — not `Any`.
- `reportAny` enabled — use `vecinita_shared_schemas.db_mapping` and `json_types` at SQL/HTTP boundaries.

### TypeScript details

- Production code: `eslint.config.js` uses `strictTypeChecked` + `projectService`.
- Tests: same config file with relaxed rules for Vitest mocks (`require-await` off, etc.).
- `npm run build` runs `tsc --noEmit` with `strict` + `noImplicitAny`.

## Consequences

- **Positive:** Consistent enforcement; docs and CI commands match; fewer silent type holes.
- **Negative:** Tests must type mocks (`vi.fn<...>()`) instead of relying on `expect.objectContaining` alone.
- **Migration:** Replace `typing.Any` with concrete types or `JsonObject`; replace `any` with unions, generics, or `unknown` + narrowing.

## Compliance

CI (`.github/workflows/ci.yml`):

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
cd apps/chat-rag-frontend && npm run lint
cd apps/data-management-frontend && npm run lint
```

The lint/format/type-check scope was extended on 2026-06-29 from `apps packages tests` to
also cover `infra` and `scripts`. Those two roots use relaxed basedpyright
`executionEnvironments` (untyped GPU/ML and ephemeral `uv run --with` deps) and dedicated
Ruff per-file-ignores for Modal/CLI patterns, while still catching real logic bugs. See
[`docs/typing-policy.md`](../typing-policy.md) for the full rationale.

## Related

- ADR-012 (monorepo packages boundary)
- `docs/test-plan.md` §CI/CD
- `.cursor/rules/strict-typing.mdc`

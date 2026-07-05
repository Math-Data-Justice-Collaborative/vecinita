# ADR-021: EV-004 Implementation Decisions

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-06-13 |
| Stage | 04-tech-plan (EV-004) |
| Deciders | User (product owner) |
| Context | F31 — Admin bilingual UI + shared frontend packages |

## Context

EV-004 (F31) introduces workspace packages `packages/frontend-i18n` and
`packages/frontend-ui`, migrates ChatRAG to shared locale/components with full Tailwind
layout, and translates all admin static UI chrome (~120+ strings). Product decisions are
in ADR-019 and ADR-020; this ADR records **implementation** choices from the 04-tech-plan
interview.

PR #60 (`fix/es-en-full-ui`) already ships ChatRAG en/es in-app; EV-004 refactors that
work into shared packages and extends bilingual UX to the admin dashboard.

## Decisions

### TP-030: Git branch — continue PR #60 branch

**Decision:** Build EV-004 on `fix/es-en-full-ui`; refactor in-app ChatRAG i18n into shared
packages on the same branch, then merge.

**Rationale:** Avoids duplicate i18n work and rebase churn; PR #60 is merge-ready with
ChatRAG locale behavior already validated.

**Consequences:** EV-004 scope includes refactoring PR #60 paths, not greenfield admin-only.

### TP-031: Package consumption — source imports via workspaces

**Decision:** npm workspaces at repo root; apps import package **source** via Vite
`resolve.alias` and tsconfig `paths` — no separate `dist/` build step for packages.

**Rationale:** Standard Vite monorepo pattern; faster dev loop; Tailwind scans package source
via PostCSS `content` globs.

**Consequences:** Both app `tailwind.config.js` files must include
`../../packages/frontend-ui/src/**/*.{tsx,ts}`; CI must install from root workspace.

### TP-032: Message typing — strict TypeScript keys

**Decision:** `frontend-i18n` exports a nested message object; `t(locale, key)` accepts
only `keyof` valid dot-paths at compile time.

**Rationale:** Prevents missing translations at build time; aligns with ADR-018 strict typing.

**Consequences:** Adding strings requires updating the typed message map; TC-067 validates
key resolution.

### TP-033: ChatRAG Tailwind — full layout migration

**Decision:** Replace ChatRAG `App.css` layout with Tailwind utilities; all shared
components from `frontend-ui`.

**Rationale:** User confirmed RD-056; consistent styling with admin and shared package.

**Consequences:** ChatRAG gains Tailwind + PostCSS devDependencies; larger EV-004 diff in
chat-rag-frontend.

### TP-034: Locale default — ES fallback

**Decision:** `detectBrowserLocale()`: `en*` → `en`, `es*` → `es`, otherwise **`es`**
(default). Storage key `vecinita.locale` shared across both DO static origins.

**Rationale:** Matches existing ChatRAG behavior (ADR-019); community-first default.

**Consequences:** No change to backend; client-only.

### TP-035: CI — root npm workspaces

**Decision:** Add root `package.json` with workspaces `apps/*` and `packages/frontend-*`;
CI frontend matrix runs `npm ci` at repo root, then per-app lint/test/build.

**Rationale:** Ensures workspace links resolve consistently; satisfies test-plan EV-004 CI note.

**Consequences:** Update `.github/workflows/ci.yml`; may add root-level `npm run` helpers.

### TP-036: Component extraction — full ADR-020 surface

**Decision:** Extract all ADR-020 components to `frontend-ui`: `LocaleProvider`,
`useLocale`, `LanguageToggle`, `ThemeToggle`, `TagFilterChips`, `TagBadge`,
`PaginationControls`, plus minimal shadcn re-exports.

**Rationale:** Single shared implementation; TC-068 covers all exports.

**Consequences:** Admin `ThemeToggle.tsx` and `TagBadge.tsx` become thin re-exports or are
removed in favor of package imports.

### TP-037: Admin translation — all static strings

**Decision:** Translate all static admin UI: Dashboard, Corpus, Health, Audit, bulk
dialogs, JobForm, DocumentAdmin, CorpusList, nav (~120+ keys).

**Rationale:** F31 acceptance (AC-F1); partial translation would fail UJ-022 sign-off.

**Consequences:** Large `admin.*` namespace in `frontend-i18n`; corpus/tag/API content
remains untranslated (R30).

### TP-038: Deploy order — simultaneous frontends

**Decision:** Deploy **chat-rag-frontend** and **data-management-frontend** in the same
release window; no backend or Modal redeploy.

**Rationale:** User preference; both depend on shared packages built in CI; no API ordering
dependency.

**Consequences:** Staging validation runs H4/H5 on both URLs in one deploy-smoke pass.

### TP-039: Connectivity regression — extend H4/H5 smoke

**Decision:** Extend `tests/smoke/test_staging_connectivity.py` and
`scripts/deploy/verify_connectivity.sh` for both frontend bundle checks (H5) and CORS
preflight (H4) — no new API routes.

**Rationale:** AC-F7; workspace packages must appear in production bundles; CORS policy
unchanged but regression guard required.

**Consequences:** M38 tasks before deploy sign-off.

## References

- ADR-019 (shared frontend i18n)
- ADR-020 (shared frontend UI)
- `docs/deployment-integration.md` §EV-004
- `docs/test-plan.md` TC-065–TC-069
- `docs/sessions/S000-internal-docs-archive/execution-plan.md` Phase 9

# Playwright UI E2E (T0-ui)

Browser-level tests complement Vitest (jsdom) and pytest API E2E (`tests/e2e/`).

## What Playwright tests here

| Vitest (component) | Playwright (interaction) |
|--------------------|--------------------------|
| Single component with mocked providers | **Real browser** — routing, focus, layout, `localStorage` |
| In-memory `fetch` mock | **Network interception** — same contracts, real `fetch` stack |
| Fast feedback on logic | **Cross-component flows** — shell ↔ panel ↔ sidebar |

**Focus:** behavior **between** components (navigation preserves state, tabs sync URL, sidebar swaps outlet, form input reaches the right panel).

**Not duplicated:** pure unit logic, isolated hook edge cases — keep those in Vitest.

## Tiers

| Tier | Marker / env | Stack | When |
|------|----------------|-------|------|
| **T0-ui** | default | `vite preview` + Playwright route mocks | CI, local QA |
| **T3-ui** | `VECINITA_STAGING_*_FRONTEND_URL` | Live staging URLs | `npm run test:ui:staging` (skipped without env) |

### Hybrid mock strategy

| Tier | Data source | When |
|------|-------------|------|
| **T0-ui** | Playwright `page.route` mocks | Every CI push (`ui-e2e` job) |
| **T3-ui** | Live staging bundles | Manual / 13-deploy-smoke when URLs set |
| **Future** | Postgres + local APIs | Optional nightly job (not in default CI) |

T0-ui proves **component interaction wiring** in a real browser. T3-ui proves **deployed bundle reachability**. Neither replaces pytest API E2E or H4–H5 CORS checks.

## Run

Prerequisites: Node 24, `npm ci`, frontend production builds.

```bash
# Full CI-parity (install, build, browsers, run)
bash scripts/ui/run_playwright.sh

# After a manual build:
bash scripts/ui/build_for_playwright.sh
npx playwright install chromium
npx playwright test
```

Makefile: `make test-ui` (build + Playwright).

## Layout

| Path | App | Interaction focus |
|------|-----|-------------------|
| `tests/ui/chat/uj001-ask-interaction.spec.ts` | ChatRAG | ChatPanel ↔ stream ↔ message list |
| `tests/ui/chat/uj024-chat-corpus-state.spec.ts` | ChatRAG | App shell state across tab navigation |
| `tests/ui/chat/uj001-chat-shell.spec.ts` | ChatRAG | Sidebar ↔ locale toggle |
| `tests/ui/chat/uj009-corpus-navigation.spec.ts` | ChatRAG | Sidebar ↔ CorpusBrowse |
| `tests/ui/admin/uj020-admin-navigation.spec.ts` | Admin | AdminLayout nav ↔ page outlet |
| `tests/ui/admin/uj041-eval-dashboard-tabs.spec.ts` | Admin | Evaluation tabs ↔ URL ↔ panels |
| `tests/ui/admin/uj026-login-page.spec.ts` | Admin | Login shell (unauthenticated) |
| `tests/ui/helpers/` | Shared | Route mocks, Supabase session seed |

Add specs as `*.spec.ts`. Map each file to a user journey in `docs/user-journeys.md` and `docs/test-plan.md`.

## CI

`.github/workflows/ci.yml` job `ui-e2e` runs T0-ui on every push/PR.

## Reports

On failure: `playwright-report/` and `test-results/` (gitignored). In CI, traces attach on retry.

## Choosing Vitest vs Playwright

| Scenario | Prefer |
|----------|--------|
| Hook returns wrong value | Vitest |
| Button click updates sibling panel | Playwright |
| CORS preflight on staging | pytest smoke / `verify_connectivity.sh` |
| Tab query param ↔ panel mount | Playwright |
| Recharts data transform | Vitest (mock recharts) |

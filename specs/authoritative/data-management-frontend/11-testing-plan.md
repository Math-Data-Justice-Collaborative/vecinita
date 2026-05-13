# data-management-frontend — Testing Plan

> Auto-generated: 2026-05-12

## Overview

Multi-layered testing with unit tests (Vitest), contract tests (Pact), integration tests, and E2E tests (Playwright).

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Unit | Vitest + Testing Library | `frontends/data-management/src/**/*.test.*` | Components, API client, auth |
| Contract | Pact (via Vitest) | `vitest.pact.config.ts` | DM API shape validation |
| Integration | Vitest | `vitest.integration.config.ts` | Multi-component flows, Modal integration |
| E2E | Playwright | `frontends/data-management/tests/e2e/` | Full browser flows (scraper journey, auth, dashboard) |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| Dashboard renders with stats | Unit | Covered |
| Login flow with auth context | Unit | Covered |
| RequireAuth route guard | Unit | Covered |
| Tags view rendering | Unit | Covered |
| Add document form | Unit | Covered |
| Scrape jobs list | Unit | Covered |
| Scraper config resolution | Unit | Covered |
| DM API routing contract | Contract | Covered |
| DM frontend ↔ DM API contract | Contract | Covered |
| RAG API error handling | Unit | Covered |
| Upstream error normalization | Unit | Covered |
| Auth smoke E2E | E2E | Covered |
| Dashboard cold start E2E | E2E | Covered |
| Scraper journey (mocked) E2E | E2E | Covered |
| Scraper journey (live) E2E | E2E | Covered |

## CI Integration

| Target | Command | Trigger |
|--------|---------|---------|
| Unit tests | `npm run test` | PR, push to main |
| Pact contract tests | `npm run test:pact` | PR, push to main |
| Lint | `npm run lint` | PR, push to main |
| E2E PR suite | `npm run test:e2e:pr` | PR (auth + dashboard + mocked scraper) |
| E2E journey (live) | `npm run test:e2e:journey:live` | Manual |

## Coverage Targets

| Metric | Target | Current |
|--------|--------|---------|
| Line coverage | 80%+ | Measured via `test:coverage` |
| Branch coverage | 70%+ | Measured via Vitest coverage-v8 |

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

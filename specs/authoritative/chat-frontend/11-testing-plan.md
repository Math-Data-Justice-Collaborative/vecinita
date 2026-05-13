# chat-frontend — Testing Plan

> Auto-generated: 2026-05-12

## Overview

Multi-layered testing strategy with unit tests (Vitest), contract tests (Pact), integration tests, and E2E tests (Playwright).

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Unit | Vitest + Testing Library | `frontends/chat/src/**/__tests__/` | Component rendering, hooks, utility functions |
| Contract | Pact (via Vitest) | `vitest.pact.config.ts` | Gateway API shape validation |
| Integration | Vitest + MSW | `frontends/chat/src/**/__tests__/*.integration.test.*` | Multi-component flows with mocked API |
| E2E | Playwright | `frontends/chat/tests/e2e/` | Full browser flows including corpus sync |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| ChatWidget renders and accepts input | Unit | Covered |
| ChatMessage displays markdown and sources | Unit | Covered |
| Stream success end-to-end | Integration | Covered |
| Agent service streaming with SSE events | Unit | Covered |
| useAgentChat hook message flow | Unit | Covered |
| useConversationStorage localStorage sync | Unit | Covered |
| AuthContext login/logout flow | Unit | Covered |
| LanguageContext switching | Unit | Covered |
| BackendSettingsContext config fetch | Unit | Covered |
| Agent API base URL resolution | Unit | Covered |
| Model registry contract validation | Contract | Covered |
| Documents dashboard integration | Integration | Covered |
| LoginPage integration flow | Integration | Covered |
| App integration (full tree render) | Integration | Covered |
| Corpus parity E2E | E2E | Covered |
| Documents readonly E2E | E2E | Covered |

## CI Integration

| Target | Command | Trigger |
|--------|---------|---------|
| Unit tests | `npm run test:unit` | PR, push to main |
| Pact contract tests | `npm run test:pact` | PR, push to main |
| Lint | `npm run lint` | PR, push to main |
| Type check | `npm run typecheck` | PR, push to main |
| E2E tests | `npm run test:e2e` | Manual / CI |

## Coverage Targets

| Metric | Target | Current |
|--------|--------|---------|
| Line coverage | 80%+ | Measured via `test:coverage:unit` |
| Branch coverage | 70%+ | Measured via Vitest coverage-v8 |

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

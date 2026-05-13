# data-management-frontend — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Key technical decisions for the data-management frontend, including resolved and pending choices.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Routing library | React Router v7 | React Router v6, TanStack Router | 2026-05-12 | Easy |
| TD-002 | API client pattern | Singleton RAGApiClient class | React Query, SWR, plain fetch | 2026-05-12 | Moderate |
| TD-003 | Mock mode | In-memory fallback when API unconfigured | MSW, json-server | 2026-05-12 | Easy |
| TD-004 | OpenAPI type generation | openapi-typescript | Manual types, GraphQL codegen | 2026-05-12 | Easy |
| TD-005 | Error handling | Retry with exponential backoff | Circuit breaker, no retry | 2026-05-12 | Easy |

### TD-002: API Client — Singleton RAGApiClient Class

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need a centralized HTTP client for DM API with retry logic, auth, and mock fallback |
| Decision | Single `RAGApiClient` class exported as `ragApi` singleton, with built-in retry, timeout, and mock mode |
| Rationale | Keeps all API logic in one file. Retry and timeout policies applied uniformly. Mock mode enables offline development. |
| Alternatives considered | **React Query** — excellent for caching/invalidation but adds dependency; current simple state management is sufficient. **SWR** — similar tradeoff. |
| Consequences | No automatic cache invalidation or stale-while-revalidate. Manual state management in components. |
| Reversibility | Moderate — extracting to React Query would require component refactoring |

### TD-003: Mock Mode — In-Memory Fallback

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Frontend should work without a running DM API for development |
| Decision | When `VITE_DM_API_BASE_URL` is empty, `RAGApiClient` returns mock data from in-memory arrays |
| Rationale | Zero-config local development. No external mock server needed. |
| Alternatives considered | **MSW** — more realistic but requires setup. **json-server** — separate process to manage. |
| Consequences | Mock data doesn't cover all edge cases. Need to remember to test with real API. |
| Reversibility | Easy — can add MSW alongside without removing mock mode |

### TD-005: Error Handling — Retry with Exponential Backoff

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | DM API on Render has cold start delays; requests need resilience |
| Decision | 3 retries with exponential backoff (500ms → 1s → 2s → 4s max). Retryable: 408, 429, 5xx, AbortError, TypeError. |
| Rationale | Handles Render cold starts gracefully. 15s timeout + 3 retries gives ~60s total window. |
| Alternatives considered | **Circuit breaker** — overkill for admin tool with single user. **No retry** — poor UX during cold starts. |
| Consequences | Slow feedback on truly failed requests (must wait for retries to exhaust) |
| Reversibility | Easy |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | MUI + Shadcn/ui coexistence | Consolidate to Shadcn/ui, keep both | Bundle size, consistency | Medium | Consolidate to Shadcn/ui |
| PTD-002 | Data fetching library | Add React Query, keep manual state | Developer experience, caching | Low | Add React Query when complexity grows |

### PTD-001: MUI + Shadcn/ui Coexistence

| Property | Value |
|----------|-------|
| Status | Pending |
| Identified | 2026-05-12 |
| Evidence | `package.json` includes both `@mui/material` and `@radix-ui/*` primitives |
| Impact | Bundle size, inconsistent styling, two component paradigms |
| Decision deadline | Before next major UI feature |

**Recommendation:** Consolidate to Shadcn/ui — aligns with Tailwind-first approach.
**Risk of continued deferral:** Bundle bloat grows, styling inconsistencies multiply.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

# Vecinita Agent — Testing Plan

> Auto-generated: 2026-05-12

## Overview

The agent service has existing test coverage primarily focused on unit tests for tools, guardrails, and API endpoints. Testing uses pytest with FastAPI's test client. The service is part of a monorepo with shared CI via GitHub Actions and Makefile targets.

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Unit | pytest | `apis/agent/tests/` | Tool logic, guardrails, response formatting, language detection |
| Integration | pytest + psycopg2 | `apis/agent/tests/` | Database search with real PostgreSQL (requires DATABASE_URL) |
| Contract | Schemathesis | CI pipeline | OpenAPI schema validation and property-based testing |
| E2E | Manual / frontend tests | `frontends/chat/` | Full flow through gateway → agent → LLM |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| FAQ exact match returns static answer | unit | covered |
| FAQ partial match with long query | unit | covered |
| Empty question returns 400 | unit | covered |
| Prompt injection blocked by guardrails | unit | covered |
| SQL injection blocked by guardrails | unit | covered |
| PII redacted in input | unit | covered |
| Toxic output blocked | unit | covered |
| Off-topic query rejected | unit | covered |
| Language detection en/es | unit | covered |
| db_search returns empty on no results | unit | covered |
| db_search tag filtering (any/all modes) | unit | covered |
| Reranking reorders by combined score | unit | covered |
| Model selection lock prevents changes | unit | covered |
| Web search Tavily fallback to DuckDuckGo | unit | covered |
| SSE stream emits correct event sequence | integration | gap |
| End-to-end RAG with real database | integration | gap |
| Rate-limit error produces localized message | unit | covered |
| Concurrent requests don't corrupt search metrics | unit | gap |
| Embedding cache LRU eviction | unit | gap |
| Health check on degraded database | integration | gap |
| Contextual follow-up with context_answer | unit | gap |

## CI Integration

| Trigger | Workflow | Command |
|---------|----------|---------|
| Push / PR | GitHub Actions | `make ci` → `make test` |
| Agent-specific | Makefile | `make test-agent` (if defined) or `pytest apis/agent/tests/` |
| Schema validation | Schemathesis | `st run --experimental=openapi-3.1 http://localhost:8000/openapi.json` |

## Coverage Targets

| Metric | Target | Current |
|--------|--------|---------|
| Line coverage | 80% | ~60% (estimated) |
| Branch coverage | 70% | ~50% (estimated) |

## Testing Gaps and Recommendations

1. **SSE streaming tests:** No automated tests for the `/ask-stream` event sequence and error handling.
2. **Database integration tests:** `db_search` tool is tested with mocks; no tests against a real pgvector-enabled PostgreSQL instance.
3. **Concurrency tests:** `ContextVar`-based search metrics isolation is not tested under concurrent load.
4. **Embedding cache tests:** LRU eviction behavior and cache hit metrics not tested.
5. **Contextual follow-up path:** The `_is_contextual_follow_up` + `_build_contextual_follow_up_answer` path lacks dedicated tests.
6. **Contract tests:** No consumer-driven contract tests between gateway and agent.

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

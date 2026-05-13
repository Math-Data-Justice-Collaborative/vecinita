# 12 — Risks and Trade-offs

> Auto-generated: 2026-05-12

## Risks

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway/agent extraction breaks existing functionality | Service downtime, lost features | Comprehensive test coverage before splitting. Feature-flag new routing to allow rollback. |
| vLLM + LlamaIndex integration produces worse RAG quality than current stack | Degraded user experience | Run parallel: keep existing providers as fallback while validating vLLM quality. Compare response quality before switching. |
| Schema-per-service migration corrupts data | Data loss | Run migration on a DB snapshot first. Keep backup. Use transaction-wrapped migration scripts. |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Import path changes during layout restructure cause cascading failures | Build failures, CI red | Automated import rewriting tools (e.g., `ruff` fix, `sed`). Run full test suite after each move. |
| Modal costs increase with vLLM GPU usage | Budget overrun | Start with small model (7B), monitor costs. Use Modal's autoscaling to scale to zero when idle. |
| Single docker-compose with profiles introduces complexity | Dev friction | Document profiles clearly. Provide `make` targets for common profiles. |
| Per-app CI workflows miss cross-service regressions | Hidden bugs | Add integration test workflow that runs on changes to any `packages/` code. |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dropping OpenAPI clients reduces type safety | Subtle API contract drift | Add lightweight contract tests (HTTP response shape validation). |
| PgAdmin on Render adds another service to manage | Minor ops overhead | Use Docker image directly, minimal config. |
| `.environments/` pattern unfamiliar to contributors | Onboarding friction | Document in README, provide `make setup-env` helper. |

## Trade-offs

| Decision | What You Gain | What You Give Up |
|----------|--------------|-----------------|
| Full rewrite vs incremental | Clean architecture, no legacy baggage | Time investment, zero production traffic during migration |
| apps/ + packages/ vs more granular layout | Simplicity, discoverability | Fine-grained CI scoping, deploy-target grouping |
| Schema-per-service vs separate DBs | Low cost, easy cross-schema queries | True data isolation, independent DB scaling |
| Modal for all GPU work | Serverless scaling, pay-per-use | Vendor lock-in to Modal, cold start latency |
| Dropping OpenAPI clients | Less maintenance, simpler builds | Auto-generated type safety for API contracts |
| Single render.yaml | One source of truth for deployment | Large file, all services coupled in one blueprint |

## Deferred Decisions

| ID | Title | Risk of Deferral | When to Decide |
|----|-------|-------------------|----------------|
| TD-007 | Python dependency management (uv vs pip vs poetry) | Low — uv is already partially used | Phase 1 (layout restructure) |
| TD-008 | LLM provider strategy (vLLM primary + fallbacks) | Low — LlamaIndex supports runtime switching | Phase 3 (vLLM integration) |
| TD-009 | LLM model selection for vLLM | Low — vLLM supports hot-swapping models | Phase 3 (vLLM integration) |

## Remaining Concerns

1. **Gateway is still large**: Even after extracting agent, gateway handles auth + routing + data CRUD + job orchestration + streaming. This is acceptable for a solo developer but may need further splitting as the team grows.

2. **Modal vendor dependency**: All GPU workloads rely on Modal. If Modal pricing changes or the service has issues, there's no fallback. Mitigation: vLLM's OpenAI-compatible API means the agent service is decoupled from the infrastructure provider — switching to self-hosted or another provider only requires changing the endpoint URL.

3. **Cold starts**: Modal serverless GPU has cold start latency (~10-30s for vLLM). First request after idle will be slow. Mitigation: Modal's keep-warm feature or a lightweight health check ping.

4. **Agent-Gateway boundary is still fuzzy**: The user skipped the detailed boundary clarification. During implementation, the exact split of gateway/src/agent/ code between the two services needs careful analysis. Recommend: start with a generous agent scope (move everything under gateway/src/agent/ to the agent service) and refine later.

5. **Data-management-api overlap**: Gateway handles data management CRUD AND there's a separate data-management-api. The boundary between these is unclear. Recommend: data-management-api owns all document/corpus CRUD, gateway proxies to it.

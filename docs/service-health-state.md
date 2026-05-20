# Service Health State

> Last updated: 2026-05-20

| Field | Value |
|-------|--------|
| Environment | staging |
| Infra overall | **PASS** |
| E2E overall | **PASS** (warm LLM); cold-start flaky |
| Overall | **PASS** |
| Last report | [2026-05-20-staging-post-deploy.md](service-health-reports/2026-05-20-staging-post-deploy.md) |
| Chat URL | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |

## Open advisories

1. Modal LLM scale-to-zero: first `/ask` after idle may exceed 60s (DO/pytest timeout) until GPU warms.
2. Data-mgmt `/health` returns 401 without proxy auth (expected).
3. Sync docs: `deploy-checklist.md`, `data-staging-state.md` D7, Phase 4 gate log still show pre-deploy pending items.

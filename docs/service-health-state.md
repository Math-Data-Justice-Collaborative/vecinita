# Service Health State

> Last updated: 2026-05-21

| Field | Value |
|-------|--------|
| Environment | staging |
| Infra overall | **PASS** (deploy drift advisory) |
| E2E overall | **PASS** (warm LLM); cold-start 504 on DO |
| Overall | **PASS** |
| Last report | [2026-05-21-staging-routine-full.md](service-health-reports/2026-05-21-staging-routine-full.md) |
| Chat URL | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Deployed SHA | `c4bc847` (repo HEAD `4d2f665` — drift) |

## Open advisories

1. Modal LLM scale-to-zero: first `/ask` after idle may hit DO **504** (~60s) until GPU warms; warm via `modal run …::LlmService.complete`.
2. Modal data-mgmt H4 CORS preflight: 401 without `Modal-Key` — **user-waived** (proxy auth before CORS).
3. DO staging not redeployed since `c4bc847`; connectivity-gates branch commits pending deploy.

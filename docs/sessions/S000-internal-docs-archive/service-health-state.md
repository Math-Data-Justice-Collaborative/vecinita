# Service Health State

> Last updated: 2026-07-28

| Field | Value |
|-------|--------|
| Environment | staging |
| Infra overall | **PASS** |
| E2E overall | **PASS** |
| Overall | **PASS** |
| Last report | [S012 service-health.md](../S012-hotfix-admin-ui-112-105/reports/service-health.md) |
| Session | S012-hotfix-admin-ui-112-105 |
| Deployed SHA (staging) | `1b60930` on `main` (includes PR #150 @ `2b3231d`) |
| Main SHA (H0ci) | `1b60930` — CI green ([run 30404116424](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30404116424)) |
| Chat URL | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |

## Open advisories

1. H4 Modal data-mgmt CORS waived (`requires_proxy_auth` at proxy).
2. Cold ask without pre-warm can exceed 60s (S012 sample ~100s); browser path uses pre-warm on mount.
3. Transient `modal_llm=error` on ChatRAG `/health` can appear during cold wake — retries recovered in S012.

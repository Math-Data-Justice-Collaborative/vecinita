# Service Health State

> Last updated: 2026-06-25

| Field | Value |
|-------|--------|
| Environment | staging |
| Infra overall | **PASS** |
| E2E overall | **PASS** |
| Overall | **PASS** |
| Last report | [S001 service-health.md](sessions/S001-modal-cold-start-snapshot/reports/service-health.md) |
| Session | S001-modal-cold-start-snapshot |
| Deployed SHA (staging) | `4f3f741` on `feat/S001-modal-cold-start-snapshot` |
| Main SHA (H0ci) | `a235707` — CI green ([run 28207027346](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28207027346)) |
| Chat URL | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |

## Open advisories

1. DO chat apps pinned to feature branch until S001 merges to `main`.
2. H4 Modal data-mgmt CORS waived (`requires_proxy_auth` at proxy).
3. 07-build T12 (web-fn hop) pending — not blocking health.
4. Cold ask without pre-warm still exceeds 60s — browser path uses pre-warm on mount (S001 fix).
5. Re-run blocking H0ci on `main` after S001 merge.

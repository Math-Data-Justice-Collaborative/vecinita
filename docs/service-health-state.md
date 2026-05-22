# Service Health State

> Last updated: 2026-05-22

| Field | Value |
|-------|--------|
| Environment | staging |
| Infra overall | **PASS** (CI secret-pattern advisory; DO SHA drift advisory) |
| E2E overall | **PASS** |
| Overall | **PASS** |
| Last report | [2026-05-22-post-hotfix-jobs-get-404.md](service-health-reports/2026-05-22-post-hotfix-jobs-get-404.md) |
| Chat URL | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Deployed SHA (repo main) | `d79a06f` (PR #36 merged) |

## Open advisories

1. Modal LLM scale-to-zero: first `/ask` after idle may hit DO NOT DO timeout on warm path (this run: 5.2s).
2. GitHub CI `Secret patterns (current tree)` failing on main — unrelated to jobs hotfix; blocks full CI green.
3. Local H0: `test_seed_load_row_counts` fails when staging DB has documents with `language=NULL`.
4. DO staging apps may not yet reflect `d79a06f` — Modal data-mgmt already on hotfix.

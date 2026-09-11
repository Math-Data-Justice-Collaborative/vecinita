# BUG-2026-09-10 — Prod CORS allows staging frontends only

> **Status:** fixed (live 2026-09-10; code guards pending commit)  
> **Date:** 2026-09-10  
> **Component:** DO `vecinita-chat-rag-backend`, `vecinita-internal-write-api`; Modal
> `vecinita-data-management` (`VECINITA_CORS_ORIGINS`)  
> **Session:** EV-prod-main-validation-e2e  
> **Corpus:** [Corpus: staging] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md]
> [Spec: .cursor/skills/connectivity-gates.md §H4]

## Error description

Production ChatRAG / internal-write-api / Modal data-management reject CORS
preflight from the **prod** frontends (`vecinita-chat-rag-frontend-jnt8o`,
`vecinita-admin-frontend-ef4ob`) with HTTP 400 `Disallowed CORS origin`.

The same prod APIs **accept** the **staging** chat FE origin
(`vecinita-staging-chat-fe-epvwo`). Browser users on prod FE get “Failed to fetch”.

Curl/`POST /api/v1/ask` without an `Origin` header still works (H1/H3 green), so
infra-only smokes miss this.

## Error logs

```text
OPTIONS https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app/api/v1/ask
Origin: https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
→ 400 Disallowed CORS origin

OPTIONS … (same API)
Origin: https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app
→ 200 Access-Control-Allow-Origin: https://vecinita-staging-chat-fe-epvwo…

Live pytest: 20 failed in tests/smoke/test_staging_connectivity.py (H4)
```

## Investigation

| Hyp | Result |
|-----|--------|
| Prod FE host wrong / renamed | Rejected — DO app list ingress matches FE hosts in bundle |
| CORS secret empty | Rejected — staging origin allowed on prod APIs |
| ADR-054 dual-env drift: staging FE origins synced into prod | **Confirmed** |
| `VECINITA_ENV=staging` on prod DO YAML | Confirmed (related; set to `production`) |

## Repro test

- Layer: live H4 — `tests/smoke/test_staging_connectivity.py` against prod URLs
- Guard: `tests/bugs/test_bug_2026_09_10_prod_cors_staging_origins.py`
- Sync guard: `validate_prod_cors_origins` in `scripts/deploy/do_apps.py`

## Fix applied

1. Live `VECINITA_CORS_ORIGINS` = prod admin + chat FE (DO + Modal + GitHub)
2. Live + YAML `VECINITA_ENV=production` on prod backends
3. Code: CORS coverage helper + sync refuse + bug/unit tests
4. Re-verified H4 OPTIONS 200 for prod FE origins; staging FE origin now 400 on prod

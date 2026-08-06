# Deploy Checklist — S028 / EV-026 Chat source UX (F72–F74)

> **Generated**: 2026-08-06  
> **Status**: **ready** (pending local `make ci-push` evidence in this turn)  
> **Deployment plan**: [deployment-integration.md](../../../deployment-integration.md) (hybrid DO + Modal; delta below)  
> **Stage**: 12-verify-deploy (S028 delta — F72–F74 / #222–#224)  
> **Branch**: `evolve/EV-026-chat-source-ux`  
> **Session**: S028-chat-source-ux  
> **env_role**: **`staging_as_live`** (sole stack = **live/prod**) — [ADR-049](../../../adr/ADR-049-single-env-staging-as-live.md) · S028-D2 / **S028-D34**  
> **Decisions**: S028-D2 · S028-D32 · S028-D33 · **S028-D34** (GHA outage → local parity + CLI deploy; mitigations + rollback approved)

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/sessions/S028-chat-source-ux/reports/verify-impl.md]

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete | **PASS** | F72 FE helper; F73 score filter; F74 migration + PATCH + admin; OpenAPI `display_title`; no `⚠️ Needs human input` in tech-plan |
| All secrets configured | **PASS** (ops) | **No new secret names** (tech-plan); existing CORS/Modal URLs. Local `prod.env` **absent** — source at 13 |
| Data assets staged | **PASS** (ops pending) | Alembic `20260806_0014_ev026_display_title` in repo; apply on live DB @ 13 |
| Resource allocation verified | **PASS** | No new Modal GPU; DO static + FastAPI redeploy only |
| Rollback plan reviewed | **PENDING** user AskQuestion | See §Rollback |
| H0c CORS unit tests | **PASS** | `pytest tests/unit/test_cors_policy.py` (+ PATCH display_title case) exit 0 @ 2026-08-06 |
| Frontend `VITE_*` ↔ API matrix | **PASS** | Existing Chat/Admin `VITE_*` rows; no new origins (tech-plan) |
| `VECINITA_CORS_ORIGINS` documented | **PASS** | `infra/do/chat-rag-backend.yaml` + `internal-write-api.yaml` (PATCH already allowed) |
| Post-deploy H4–H5 documented | **PASS** | `bash scripts/deploy/verify_connectivity.sh` (+ Chat SourceList / admin rename smokes @ 13) |
| Tip CI green (RA-009) | **WAIVED** (S028-D34) | GitHub Actions outage — remote `ci.yml` not required; full local `make ci-push` + CLI deploy instead |

## Live stack drift (must clear at 13)

| Field | Value |
|-------|-------|
| Live stack last smoke | `c942971` (S026) |
| EV-026 tip | `8537690` (not pushed; + local docs delta) |
| Drift | **YES** — redeploy Chat FE, Admin FE, write API, chat-rag BE + Alembic before H4–H5 |
| `env_role` | **`staging_as_live`** — treat DO/Modal “staging” URLs as **production** |

## S028-specific deploy surfaces

| Surface | Change | Deploy / apply |
|---------|--------|----------------|
| DO chat-rag-frontend | F72 `SourceList` + shared URL helper | Static rebuild/redeploy |
| DO chat-rag-backend | F73 relevance-gated `sources[]` | DO CD / app redeploy |
| DO internal-write-api | F74 `PATCH` `display_title` + DTO | DO CD / app redeploy |
| DO admin frontend | F74 DocumentAdmin rename | Static rebuild/redeploy |
| DO Managed Postgres | `documents.display_title` | `alembic upgrade head` **before** write API relies on column |
| Modal apps | None required for F72–F74 | No embed/LLM pin change this cycle |
| packages (`rag`, `frontend-ui`) | Ship with BE/FE images | via app redeploys |

### Redeploy order (live = prod)

1. **Alembic** `upgrade head` on live Postgres (`20260806_0014_ev026_display_title`)
2. DO **internal-write-api** (PATCH `display_title`)
3. DO **chat-rag-backend** (F73 sources filter + coalesce packing)
4. DO **chat-rag-frontend** (F72 citation href filter)
5. DO **admin frontend** (F74 rename UI)
6. Optional: `sync-all-secrets` / `modal_url_validate` if any Modal URL churn (not expected)
7. **H4–H5** + UJ-077–079 live smokes @ **13** (AskQuestion — QA-S028-003)

### Post-deploy connectivity (13)

```text
set -a && source prod.env && set +a
uv run python scripts/deploy/modal_url_validate.py   # if touching Modal URLs
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/verify_connectivity.sh           # H4–H5
# Manual: ChatRAG ask → sources hrefs; Admin DocumentAdmin rename → citation title
```

## Agent results (Phase 1)

### Configuration (Agent 1) — PASS

| Item | Status |
|------|--------|
| F72 SourceList / `isSafeHttpUrl` | OK in repo |
| F73 retrieve post-filter | OK — UJ-078 T0 |
| F74 migration + PATCH + OpenAPI | OK |
| ADR-051 Accepted | OK |
| No new secrets / CORS origins | OK (tech-plan) |

### Secrets (Agent 2) — PASS (ops)

| Category | Status |
|----------|--------|
| New secret names | None |
| Modal URL shape | Unchanged; validate if syncing |
| Live `prod.env` / `modal secret list` | SKIPPED locally (`prod.env` absent) |

### Data & volumes (Agent 3) — PASS (ops)

| Asset | Status |
|-------|--------|
| Alembic `display_title` | In repo — apply @ 13 |
| Corpus | No bulk mutation in EV-026; rename is per-doc operator action |

### Resources (Agent 4) — PASS

| Check | Status |
|-------|--------|
| New GPU / Modal scale | N/A |

### CI / CD (Agent 5) — **WAIVED remote** (S028-D34)

| Check | Status |
|-------|--------|
| Remote `ci.yml` on tip | **WAIVED** — GHA outage |
| Local full parity `make ci-push` | **Required** this turn before 13 |
| Deploy path | **CLI** (`doctl` / app update / alembic) — not Actions CD |
| Hybrid api+worker (not Cognichem job template) | N/A |

### Browser connectivity (Agent 6) — PASS (unit)

| Check | Status |
|-------|--------|
| H0c `test_cors_policy.py` | PASS |
| PATCH document metadata CORS | Covered |
| `verify_connectivity.sh` / smoke tests | Present |
| Live H4–H5 | Deferred to 13 (QA-S028-003) |

### Modal / DO secret parity (Agent 7) — PASS

| Check | Status |
|-------|--------|
| `infra/do/*` Modal embed/LLM URLs | Declared |
| Sync / validate scripts | Present |

## Failure Mitigations (pending user)

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Tip never remote-CI-tested / GHA outage | Commit → full local `make ci-push` → CLI deploy @ 13 | **approved** S028-D34 |
| 2 | Live stack still on `c942971` | Redeploy order above from tip before H4–H5 (CLI) | **approved** S028-D34 |
| 3 | Alembic after write API → 500 on PATCH | Migrate **first**; smoke PATCH before FE cutover | **approved** S028-D34 |
| 4 | Stale FE bundles (old SourceList / no rename) | Redeploy both static apps; H5 bundle check @ 13 | **approved** S028-D34 |
| 5 | CORS miss after backend redeploy | Existing origins + H0c; H4 @ 13 | **approved** S028-D34 |
| 6 | Accidental corpus wipe | No truncate; F74 is PATCH metadata only | **approved** S028-D34 |

## Rollback (**approved** S028-D34)

- **Code:** Redeploy prior DO app versions / static builds from last-known-good (`c942971` / last green `main` pre-merge).
- **Schema:** `display_title` is nullable additive — safe to leave column; stop writing via prior write-api image if needed. Do **not** drop column in panic without AskQuestion.
- **Operator data:** Clear bad `display_title` with PATCH `null` (AC-SU10) rather than DB surgery.
- **Never** TRUNCATE corpus (corpus-db-safety / no-live-prod-corpus-push).
- **Last known good (live smoke):** `c942971` (S026).

## Sign-Off

- [x] User approved implementation (11-verify-impl S028-D32)
- [x] Failure mitigations approved (S028-D34)
- [x] Rollback plan approved (S028-D34)
- [x] Tip CI green **waived** — local `make ci-push` + CLI deploy (S028-D34 / GHA outage)
- [x] Deploy strategy verified — **ready for 13** after local parity evidence

## Next step

`make ci-push` (this turn) → **13-deploy-smoke** AskQuestion — live/prod CLI redeploy + H4–H5 (QA-S028-003).

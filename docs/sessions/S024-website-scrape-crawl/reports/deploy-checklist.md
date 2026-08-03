# Deploy Checklist — S024 / EV-022 Website scrape & crawl (F59–F61)

> **Generated**: 2026-08-03  
> **Status**: **approved** — S024-D47 (mitigations + rollback + JS Decision A)  
> **Mode**: DELTA — Path A (Modal DM + DO internal-write + Admin FE + Alembic `0011`)  
> **Branch tip**: `evolve/EV-022-website-scrape-crawl` @ `aeb76a9`  
> **Deployment plan**: `docs/deployment-integration.md` + ADR-045 + [tech-plan-delta](./tech-plan-delta.md)  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **approved** F59–F61 (S024-D46)

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | Path A locked; scrape/crawl defaults in `infra/vecinita.yaml`; no `⚠️ Needs human input` |
| 2 | Secrets | **PASS / N/A** | No new F59–F61 secrets (S024-D19); reuse Modal/DO set |
| 3 | Data / volumes / migration | **PASS** (ship-path) | Additive Alembic `20260803_0011`; **must apply** on DO Postgres (QA-S024-A06); no new Modal volume |
| 4 | Resources | **PASS** | Modal **CPU** scrape worker; no new GPU class |
| 5 | Template / CI deploy | **PASS** | Existing `deploy-modal.yml` + `deploy-digitalocean.yml`; no new workflow |
| 6 | Browser connectivity | **PASS** | H0c **17 passed / 12 skipped**; no new CORS/VITE (S024-D20); H4–H5 at 13 |
| 7 | Modal / DO secret parity | **PASS** | URL validators + infra SECRET placeholders unchanged |

### New / changed ship surfaces

| Surface | Change |
|---------|--------|
| Modal `vecinita-data-management` | scrape/crawl pipeline; image deps `trafilatura`, `pypdf`, `playwright` |
| DO `vecinita-internal-write-api` | `GET /corpus/tree` + nested source columns |
| DO `vecinita-admin-frontend` | JobForm crawl options + Corpus tree UI |
| DO Postgres | Alembic `20260803_0011_ev022_nested_source_fields` |

### Env / config (no new secrets)

| Key | Default | Ship expectation |
|-----|---------|------------------|
| `scrape_*` / crawl limits | RPS 0.5, depth≈2, pages≈25, `js_render: auto` | Config defaults; not secrets |
| `VECINITA_CORS_ORIGINS` / `VITE_*` | Existing Admin SPA | **Unchanged** (S024-D20) |

### Redeploy order (staging Path A)

1. Merge evolve tip → `main` (CI green on PR)  
2. DO CD: Alembic upgrade → secret sync → force deploy (write API + Admin FE)  
3. Modal CD: redeploy `vecinita-data-management`  
4. Smokes at 13: `do_verify` → H1–H3 → Admin JobForm crawl + Corpus tree → H4–H5 → optional live crawl (S024-D24)

## Failure mitigations (**approved** — S024-D47)

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Modal DM image build failure (trafilatura/playwright pip) | deploy-preflight `build-smoke`; watch Modal deploy logs | **approved** |
| 2 | Secret missing | No new scrape secrets; reuse set — `check_do_required_secrets` / `do_verify` at 13 | **approved** |
| 3 | Alembic `0011` fail / not applied | DO CD Alembic step; confirm head on staging DB before tree smokes | **approved** |
| 4 | Auth/CORS / browser | H0c PASS; H4–H5 via `verify_connectivity.sh` after FE + write redeploy | **approved** |
| 5 | Cold start / Playwright browsers | **Decision A** — ship static scrape/crawl/tree; JS-render Chromium path is **follow-up** (pip present; `fetch_url` not launching browser yet) | **approved** |
| 6 | Wrong Modal embed/LLM URL | Unchanged by EV-022; still `modal_url_validate` + `do_verify` at 13 | **approved** |

### JS-render Decision A (S024-D47)

Ship Path A for **static** scrape + crawl + tree now. Full Playwright-in-worker browser path (ADR-045 / S024-D7) tracked as **follow-up** before claiming heavy JS-site coverage. Smoke with static pages; `auto`/`always` may not escalate until wire-up.

## Rollback (**approved** — S024-D47)

| Item | Plan |
|------|------|
| Modal | Redeploy prior `vecinita-data-management` revision |
| DO write + Admin FE | Redeploy prior app deployments / revert merge on `main` |
| Alembic | Downgrade `20260803_0011` only if required (nullable cols — prefer leave forward) |
| Corpus | No re-embed required for schema-only nested fields |
| Last known good | Prior `main` tip before EV-022 merge |

## Connectivity readiness

| Gate | Status |
|------|--------|
| H0c CORS unit | **PASS** |
| VITE / CORS matrix | **PASS** — no new origins |
| H4–H5 | Planned at **13** via `scripts/deploy/verify_connectivity.sh` |
| Live crawl smoke (T3) | Planned at **13** (S024-D24) |

## Sign-Off (**S024-D47**)

- [x] User approved implementation (11-verify-impl — S024-D46)
- [x] Failure mitigations approved
- [x] Rollback plan approved
- [x] JS-render Decision A recorded (static ship; browser path follow-up)
- [x] Deploy strategy verified → ready for 13

## AC ship notes

| AC | At 12 | At 13 |
|----|-------|-------|
| AC-SC1–7,9–11 | met at T0 (+ AC-SC8 CI-gated) | live Admin + write + Modal confirm |
| AC-SC8 | CI-gated locally | confirm `GET /corpus/tree` on staging |
| AC-SC12 | **held** | remains out of scope |
| JS-render (S024-D7) | **Decision A** — follow-up | static smoke; JS path not gate |

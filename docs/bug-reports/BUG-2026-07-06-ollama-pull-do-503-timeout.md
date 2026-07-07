# BUG-2026-07-06 — Ollama model pull 503 (DO connection timed out)

> Status: **verifying** (production pull 202 confirmed 2026-07-06)  
> Feature: **F38** (playground model download, EV-010/S009)  
> Component: `apps/internal-write-api` → Modal `vecinita-ollama` (`POST /internal/v1/models/ollama/pull`)

## Error description

Super-admin **Download** on the Evaluation playground triggers `POST /internal/v1/models/ollama/pull`.
DigitalOcean App Platform returns an **HTML 503** error page (`via_upstream`, `connection_timed_out`) instead
of the expected JSON `202 Accepted` with `job_id`.

## Error logs

```text
HTTP 503 via_upstream — DigitalOcean App Platform error page:

  Error code: 503
  via_upstream (503 -)
  App Platform failed to forward this request to the application.
  connection_timed_out

Request:
  POST https://vecinita-internal-write-api-icze4.ondigitalocean.app/internal/v1/models/ollama/pull
  Body: {"model_id":"qwen2.5:0.5b-instruct"}
  Authorization: Bearer <redacted>
  Referer: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/
  Origin: cross-site CORS from admin frontend
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Error / crash — 503 HTML on every pull attempt |
| Where | Production admin frontend (Evaluation playground download) |
| When | After last deploy (S009 / F38) |
| Frequency | Every time |
| Repro env | Production and local |
| Severity | Critical — cannot download Ollama models |
| Evidence | User pasted fetch + HTML 503 |
| Tried | Nothing |

## Remediation path

**local-first** — fix locally, deploy to production only after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Original DO 503 HTML gone — pull returns JSON **202** with `job_id` |
| Verification checks | Full main CI parity (local) + GitHub CI on PR/main after merge |
| Monitoring | User watches production after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | DO edge timeout — slow Modal cold start | **Rejected** — production pull fails in **~0.23s** (not a hang) |
| H2 | `ollama_models` client not wired → app JSON 503, DO wraps as HTML | **Confirmed** — live DO spec lacks `VECINITA_MODAL_OLLAMA_URL`; `vecinita-ollama` Modal app not deployed |
| H3 | internal-write-api container unhealthy | **Rejected** — `/health` 200 in 0.1s; GET `/models/ollama` 200 in 0.16s |
| H4 | List fallback masks missing Ollama — UI shows Download for `available:false` catalog entries | **Confirmed** — list returns 12-model catalog with vLLM fallback; pull still 503 |
| H5 | CORS / auth failure | **Rejected** — super-admin JWT accepted on list; pull reaches upstream 503 path |

**Production evidence (2026-07-06):**

- `GET /internal/v1/models/ollama` → `200` JSON (catalog; `qwen2.5:0.5b-instruct` `available:false`)
- `POST /internal/v1/models/ollama/pull` → DO HTML 503/504 in ~0.23s (`via_upstream`, misleading `connection_timed_out` text)
- Live DO `vecinita-internal-write-api` env keys: **no** `VECINITA_MODAL_OLLAMA_URL` (only `VECINITA_MODAL_PROXY_KEY`, `VECINITA_MODAL_LLM_URL`, …)
- Modal workspace apps: **no** `vecinita-ollama` deployed (only embedding, llm, data-management)

## Root cause

**Config / infra drift:** F38 pull requires `VECINITA_MODAL_OLLAMA_URL` on internal-write-api and a deployed Modal `vecinita-ollama` app. Repo spec (`infra/do/internal-write-api.yaml`) and `do_apps.py` sync list include the key, but **production DO was never synced** after F38 wiring. GET list was fixed (BUG-2026-07-05) to vLLM-fallback `200`, so the playground shows downloadable models; POST pull still hits unwired client → JSON `503` → DO HTML error page.

Classification: **Config / infra** (primary) + **UX drift** (list OK / pull broken).

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F38 | In scope — pull requires Modal Ollama + DO URL (deploy prerequisite) |
| `docs/api-contract.md` §POST pull | Spec: `503` when Ollama client not configured; `202` when wired — **code matches spec** |
| `docs/deployment-integration.md` | Requires `VECINITA_MODAL_OLLAMA_URL` on internal-write-api — **live DO drift** |
| `infra/do/internal-write-api.yaml` | Declares `VECINITA_MODAL_OLLAMA_URL` — **repo OK, production not synced** |
| `docs/adr/ADR-036-ev010-playground-model-download.md` | Pull proxied to Modal ASGI — **Modal app not deployed** |

**Blocking drift:** none — implementation matches spec; **production deploy state** does not.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Unconfigured pull JSON 503 + list 200 + infra spec guard | `tests/bugs/test_bug_2026_07_06_ollama_pull_do_503_timeout.py` | green (documents symptom) |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-06 | Write repro tests — unconfigured pull 503, list 200, DO spec declares OLLAMA URL | GREEN (symptom encoded) |
| 2 | 2026-07-06 | User confirmed repro matches production DO HTML 503 | confirmed |
| 4 | 2026-07-06 | Deploy vecinita-ollama + sync VECINITA_MODAL_OLLAMA_URL to DO | Production pull **202** in 3.5s |

## Fix

1. **`infra/modal/ollama_app.py`**: Mount `vecinita-ollama` Modal secret on ASGI; add `zstd` apt package for Ollama installer.
2. **`scripts/deploy/modal.sh`**: Deploy `vecinita-ollama` in Modal deploy sequence.
3. **`scripts/deploy/modal_url_validate.py`**: Validate `VECINITA_MODAL_OLLAMA_URL` host pattern.
4. **`scripts/check_do_required_secrets.sh`**: CI guard for Ollama URL in write-api spec + `do_apps.py` sync list.
5. **Production ops (applied)**: Created Modal secret `vecinita-ollama`; `modal deploy infra/modal/ollama_app.py`; synced `VECINITA_MODAL_OLLAMA_URL` + proxy key to DO internal-write-api via `do_apps.py sync-secrets`.

## Verification

### Layer 1 — Automated

- [x] Repro tests pass (`tests/bugs/test_bug_2026_07_06_ollama_pull_do_503_timeout.py` — 4 tests)
- [x] `scripts/check_do_required_secrets.sh` pass
- [ ] Full CI parity (local) before PR

### Layer 2 — Reproduction

- [x] Production `POST …/ollama/pull` → JSON **202** `{"status":"pulling",…}` (was DO HTML 503)

### Layer 3 — Pre-deploy smoke

- [x] Direct Modal Ollama pull → 202
- [x] DO spec includes `VECINITA_MODAL_OLLAMA_URL` after sync

### Layer 4 — Production

- [x] Deployed DO internal-write-api (deployment ACTIVE 2026-07-06)
- [x] Production pull returns 202 — agent verified
- [ ] User confirms Download in admin UI

### CI

- [ ] Local parity before PR
- [ ] PR branch CI after push
- [ ] Main CI after merge

## Post-deploy monitoring

*(pending)*

## Prevention & countermeasures

*(pending Phase 5)*

## Cursor rule

*(pending Phase 5.1)*

## Regression prevention

*(pending)*

## Follow-ups

*(pending)*

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-07-06 |
| Investigation start | 2026-07-06 |

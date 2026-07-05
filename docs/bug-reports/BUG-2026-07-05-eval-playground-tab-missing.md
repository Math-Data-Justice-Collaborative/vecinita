# BUG-2026-07-05 — Evaluation Playground tab missing on production admin

**Status:** verifying  
**Severity:** critical  
**Feature:** F37 — Eval playground (S008 / EV-009)  
**Reported:** 2026-07-05

## Error description

Production admin frontend (`vecinita-admin-frontend`): the **Playground** tab is not visible
on `/evaluation`. User sees Runs, Dashboard, Explore, and Criteria only. Playground was
shipped in S008 (PR #119) but never appeared after deploy.

## Error logs

DO App Platform build log (`vecinita-admin-frontend`, deployment `27eb93ce`, 2026-07-05):

```
> prepare
> husky

sh: 1: husky: not found
npm error code 127
npm error command failed
npm error command sh -c husky
ERROR: failed to build: exit status 127
 ✘ build failed
```

Production bundle probe (2026-07-05):

```
curl -sS .../assets/index-DGlevZLG.js | rg eval-tab-
# eval-tab-criteria, eval-tab-dashboard, eval-tab-explore, eval-tab-runs
# (no eval-tab-playground)

Last-Modified: Thu, 02 Jul 2026 13:52:48 GMT  (ACTIVE deployment from Jul 2)
```

Local build at `main` includes `eval-tab-playground` and `evaluation-playground`.

## Symptoms & reproduction

| Field | User report |
|-------|-------------|
| Symptom type | Missing UI — Playground tab label not in tab bar |
| Where | Production DO admin (`vecinita-admin-frontend-ef4ob.ondigitalocean.app`) |
| When started | After last deploy — never worked in this environment |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical |
| Tried | Nothing |

## Investigation

| Time | Finding |
|------|---------|
| 2026-07-05 | Playground tab present unconditionally in `EvaluationPage.tsx` (L287–289). Not a UI conditional/role gate. |
| 2026-07-05 | Production JS bundle lacks `eval-tab-playground`; local `npm run build` includes it. |
| 2026-07-05 | ACTIVE DO deployment for admin FE: `6864debf` (2026-07-02). Four deployments since S008 merge (`b79138f`, Jul 5) all **ERROR**. |
| 2026-07-05 | Build failure: root `package.json` `"prepare": "husky"` added in S008 (`b79138f`); DO `npm ci` runs prepare but `husky` binary not on PATH. |
| 2026-07-05 | `Deploy DigitalOcean` workflow reports **success** after *starting* deployments — does not wait for build phase; stale bundle stays live. |
| 2026-07-05 | Same husky failure affects `vecinita-chat-rag-frontend` (deployments ERROR since Jul 5). |

## Root cause

**Config / infra** — DO static-site builds fail on root `prepare` → `husky` (not found). GitHub
CD workflow marks deploy job success when deployment is *queued*, not when build completes.
Production serves last successful build (Jul 2), which predates S008 Playground.

## Hypotheses tested

| # | Hypothesis | Result |
|---|------------|--------|
| 1 | Tab clipped by CSS overflow | Rejected — tab not in production bundle at all |
| 2 | Role-gated Playground tab | Rejected — no conditional in `EvaluationPage.tsx` |
| 3 | Stale deploy / build failure | **Confirmed** — DO ERROR + Last-Modified Jul 2 |

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/user-journeys.md` UJ-045 (playground) | **Implementation drift** — code on main, prod not deployed |
| F37 eval playground | pass (code) · deploy blocked |
| `infra/do/data-management-frontend.yaml` | **Implementation drift** — build_command lacks `HUSKY=0` |

## Remediation path

**local-first** — fix locally, deploy to production only after user approval.

## Repro test

- Path: `tests/bugs/test_bug_2026_07_05_eval_playground_deploy_husky.py`
- Status: GREEN (2026-07-05) — was RED before fix

## Verification plan

| Criterion | Check |
|-----------|-------|
| Success | Playground tab visible on production `/evaluation` after redeploy |
| Layer 1 | Full main CI parity (local) |
| Layer 4 | User watches production after deploy |

## Fix

1. `scripts/prepare-husky.mjs` — skip husky when `HUSKY=0` or binary unavailable (DO buildpack).
2. `package.json` — `"prepare": "node scripts/prepare-husky.mjs"` (replaces bare `husky`).
3. `infra/do/data-management-frontend.yaml` + `chat-rag-frontend.yaml` — `build_command: HUSKY=0 npm ci && npm run build`.

Note: live DO app spec still has `build_command: npm ci && npm run build` until spec sync; merged
`prepare-husky.mjs` on `main` is sufficient for the next successful DO git build.

## Verification

### Layer 1 — Automated
- [x] Repro test red→green
- [x] `prepare-husky.mjs` exits 0 without husky on PATH
- [ ] Full CI parity (local) — pending before PR
- [ ] PR branch CI — pending push

### Layer 4 — Production
- [ ] DO admin-frontend deployment reaches ACTIVE (not ERROR)
- [ ] Production bundle contains `eval-tab-playground`
- [ ] User confirms Playground tab visible

# BUG-2026-05-22 — Chat cold-start Network Error

> Status: **resolved** (PR #37; DO chat-rag-frontend 2026-05-22; user verified)
> Feature: **F2** (ChatRAG ask / stream)  
> Component: `apps/chat-rag-frontend`, `apps/chat-rag-backend`, Modal `vecinita-llm`

## Error description

First chat question after Modal LLM scale-to-zero shows browser **Network Error** in the
ChatRAG frontend. Manual retry succeeds once the LLM container is warm.

## Error logs

```text
# Prior service health (2026-05-21) — cold LLM path
POST /api/v1/ask → DO gateway 504 after ~68s (scale-to-zero)
POST /api/v1/ask (after warm) → 200 in ~14.6s

# User report (2026-05-22)
# Symptom: "Network Error" in chat UI on cold start
# Retry: works on second attempt
# DevTools: partial evidence (user has not pasted full capture)
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error — Network Error / failed fetch on first ask |
| Where | Production — ChatRAG frontend → DO backend → Modal LLM |
| When | After last deploy; every cold start after idle |
| Frequency | Every time on cold start |
| Repro env | Production only |
| Severity | High — bad UX; retry works |
| Evidence | Partial — user confirms retry works; health reports document 504 |
| Tried | Manual retry (works) |

## Remediation path

**local-first** — fix locally, deploy only after user approval.

## Investigation

### Timeline

| When | Event |
|------|-------|
| 2026-05-20 | Deploy smoke: H3 cold-start 504 until LLM warm (~19s) |
| 2026-05-21 | Service health: cold ask 504 @ ~68s; warm ask PASS @ 14.6s |
| 2026-05-22 | User hotfix intake: improve cold-start handling for chat |

### Hypotheses

| # | Hypothesis | Status |
|---|------------|--------|
| H1 | DO App Platform idle timeout (~60s) < Modal vLLM cold start → 504 → browser "Network Error" | Likely |
| H2 | Frontend has no retry / warm-up UX; raw fetch failure surfaces as generic error | Likely |
| H3 | Backend `VECINITA_REQUEST_TIMEOUT_S=60` too short for cold path | Possible |
| H4 | Embedding cold start (separate Modal service) adds latency | Possible |

### Root cause

**Confirmed:** Modal vLLM cold start can exceed DO gateway timeout (~60s), producing HTTP 504
or browser network failure. `streamAsk` had no retry on transient failures; `ChatPanel`
surfaced raw errors (e.g. "Failed to fetch") immediately with no warm-up UX.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Retry policy contract | `tests/bugs/test_bug_2026_05_22_chat_cold_start_network_error.py` | green |
| streamAsk auto-retry | `apps/chat-rag-frontend/src/api/ask.test.ts` | red → green |
| ChatPanel warm-up UX | `apps/chat-rag-frontend/src/test/ChatPanel.test.tsx` | green |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Intake + bug report created | — |
| 2 | Vitest repro RED (no retry on network/504) | fail as expected |
| 3 | Fix: retry + warm-up message in ask.ts / ChatPanel | green |

## Verification plan

| Field | Value |
|-------|--------|
| Success criterion | Cold start no longer shows "Network Error"; user sees warm-up message and gets answer |
| Checks | Unit tests + user repro on staging cold start |
| Monitoring | 15-service-health follow-up after deploy |

## Fix

- **`packages/shared-schemas/vecinita_shared_schemas/transient_http.py`**: shared retry
  policy (network errors + 502/503/504; 3 attempts; 2.5s delay).
- **`apps/chat-rag-frontend/src/api/ask.ts`**: auto-retry `streamAsk`; friendly
  `formatAskFailureMessage`; `COLD_START_STATUS_MESSAGE`.
- **`apps/chat-rag-frontend/src/components/ChatPanel.tsx`**: show warm-up status during
  retries; friendly errors instead of raw network messages.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] Bug repro tests pass
- [x] Frontend vitest + lint pass
- [x] Full pytest (bugs + unit)
- [x] PR branch CI green (26316165050)
- [x] Main CI green (26316208500)

### Layer 2 — Reproduction

- [x] User confirmed staging cold-start UX fixed

### Layer 3 — Pre-deploy smoke

- [x] DO chat-rag-frontend redeploy (ec573222)

### Layer 4 — Production

- [x] User confirms cold-start UX improved

### CI

| Check | Result | URL |
|-------|--------|-----|
| Local parity | pass (vitest + bugs) | — |
| PR branch CI | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/26316165050 |
| Main CI | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/26316208500 |

## Prevention & countermeasures

| Question | Answer |
|----------|--------|
| Recurrence risk | Possible on similar timeout/retry gaps |
| Detect earlier | Main CI (frontend vitest on PR) |
| Automated | Bug repro tests (done) |
| Code hardening | Raise `VECINITA_REQUEST_TIMEOUT_S` default to 120 (follow-up) |
| Process | connectivity-gates failure signature row |
| When / who | Now / agent |

## Post-deploy monitoring

15-service-health follow-up scheduled per user verification plan.

## Cursor rule

`.cursor/rules/chat-rag-cold-start-retry.mdc`

## Follow-ups

- Ops: warm LLM before demos (`modal run infra/modal/llm_app.py::LlmService.complete`)


# BUG-2026-05-21 — stream_tokens TypeError (Function not callable)

> Status: **resolved**  
> Feature: **F6** (self-hosted LLM on Modal)  
> Component: `infra/modal/llm_app.py` (`vecinita-llm`)

## Error description

`POST /generate/stream` returns HTTP 200, runs ~61s, then the SSE stream crashes with:

`TypeError: 'Function' object is not callable` at `stream_tokens` line 128 when calling `self.complete(...)`.

Chat frontend streaming is blocked in production.

## Error logs

```
POST /generate/stream -> 200 OK  (duration: 61.7 s, execution: 61.4 s)
...
File "/root/llm_app.py", line 173, in event_stream
    for token in service.stream_tokens.remote_gen(
...
File "<ta-01KS6DAPJ20WBWACSC3CCXG0TF>:/root/llm_app.py", line 128, in stream_tokens
TypeError: 'Function' object is not callable
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error / crash on SSE stream |
| Where | Production Modal `vecinita-llm`; Chat frontend |
| When | After last deploy |
| Frequency | Every time on `/generate/stream` |
| Repro env | Production (Modal SSE) |
| Severity | Critical |
| Evidence | User stack trace (above) |
| Tried | Nothing yet |

## Remediation path

**local-first** — deploy to production only after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `stream_tokens` calls `self.complete()` but `@modal.method` wraps `complete` as Modal `Function` — not callable in-process | **Confirmed** — `llm_app.py:128` |
| H2 | `/generate` (non-stream) works because it uses `service.complete.remote()` from ASGI, not direct call | Consistent |
| H3 | Frontend/CORS issue | Ruled out — server-side TypeError in GPU worker |

## Root cause

Inside `LlmService.stream_tokens`, `self.complete(prompt, ...)` invokes the Modal method wrapper as a plain Python callable. Modal exposes `complete` as a `Function` object; only `.remote()`, `.remote_gen()`, or `.local()` are valid. Intra-class calls must use a private helper or `.local()`.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F6 | In scope |
| `docs/api-contract.md` POST `/generate/stream` | SSE `token` + `done` events — fix restores contract |
| `docs/deployment-integration.md` | `vecinita-llm` on T4 — unchanged |

**Blocking drift:** none.

## Repro test

| Test | Path | Status |
|------|------|--------|
| `stream_tokens` must not call `self.complete(...)` directly | `tests/bugs/test_bug_2026_05_21_stream_tokens_function_not_callable.py` | red → green (user confirmed) |

## Fix

- Added `_generate_text()` on `LlmService` for in-container vLLM generate.
- `complete` and `stream_tokens` call `_generate_text()` instead of `self.complete(...)`.

## Verification plan

| User choice | Value |
|-------------|--------|
| Success | Original TypeError gone; Chat stream completes |
| Checks | Unit + Modal smoke on `/generate/stream` |
| Follow-up | 15-service-health after deploy |

| Layer | Check |
|-------|--------|
| L1 | `pytest tests/bugs/test_bug_2026_05_21_stream_tokens_function_not_callable.py` + full suite |
| L2 | User repro Chat `/generate/stream` |
| L3 | `modal deploy infra/modal/llm_app.py` + POST `/generate/stream` — **pass** (200, 11 tokens, `done`) |
| L4 | User confirm + 15-service-health follow-up |

## TDD iteration log

| Run | Action | Result |
|-----|--------|--------|
| 1 | AST repro test | red |
| 2 | `_generate_text` helper | green |

## Interview record (Phase 5)

| Question | Answer |
|----------|--------|
| Recurrence risk (Modal class) | Very likely as more `@modal.method` added |
| Detect earlier | AST repro test in `tests/bugs/` |
| Automated | Existing bug repro sufficient |
| Cursor rule | Create now |

## Prevention & countermeasures

| Action | Status |
|--------|--------|
| `_generate_text()` shared helper pattern | **done** (fix) |
| AST regression `test_bug_2026_05_21_stream_tokens_function_not_callable.py` | **done** |
| Cursor rule `.cursor/rules/modal-llm-method-calls.mdc` | **done** |
| Optional `modal run` in staging checklist | deferred |

## Cursor rule

- **Path:** `.cursor/rules/modal-llm-method-calls.mdc`
- **Declined:** no

## Follow-ups

- Pair with BUG-2026-05-20 shutdown rule on `llm_app.py` edits.

# BUG-2026-05-21 — Repetitive generic assistant answer on ChatRAG frontend

> Status: **verifying** (local L1 pass; staging deploy pending user approval)  
> Feature: **F1** (bilingual Q&A), **F2** (streaming), **F6** (self-hosted LLM)  
> Components: `apps/chat-rag-frontend`, `apps/chat-rag-backend`, `infra/modal/llm_app.py`, `packages/llm-client`

## Error description

On **staging ChatRAG frontend**, the assistant message is a long repetition of generic chatbot boilerplate instead of a community Q&A answer, e.g.:

> Hello, how can I assist you today? I'm here to help with any questions you might have. How can I assist you? … (repeats many times)

**Sources** panel shows corpus citations such as **"Write API test (0.01)"** (duplicate entries) — integration-test fixture title with very low relevance score.

User impact: **critical** — chat appears unusable.

## Error logs

```
(none yet — user will paste question text, screenshot, or Modal/DO request IDs)
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Wrong output — repetitive / nonsense streamed answer |
| Where | Staging ChatRAG frontend (DigitalOcean) |
| When | After last deploy |
| Frequency | User to clarify (selected "I'll explain" in intake) |
| Repro env | Staging frontend only |
| Severity | Critical (user) |
| Evidence | Partial — answer text in chat; more pending |
| Tried | Cleared chat history / refreshed page |

## Remediation path

**local-first** — deploy Modal LLM + DO ChatRAG backend after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Frontend duplicates tokens or messages | **Unlikely** — `useChatHistory.appendAssistantToken` appends each SSE token once; no loop in `ChatPanel.tsx` |
| H2 | Backend streams duplicate SSE events | **TBD** — inspect `/api/v1/ask/stream` and Modal `/generate/stream` |
| H3 | LLM repetition degeneration (max_tokens=512, no repetition_penalty, raw prompt on Qwen2.5-1.5B-Instruct) | **Confirmed** |
| H4 | Irrelevant retrieval (test corpus "Write API test", score ~0.01) poisons context | **Confirmed** — no `score_threshold` on `ChatRagService` |
| H5 | Missing chat template for instruct model | **Confirmed** — plain completion triggers generic assistant loops |

### Agent notes (pre-repro)

- Staging URL (from service-health 2026-05-21): https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
- Prior hotfix BUG-2026-05-21 fixed `stream_tokens` TypeError — streaming may work now but model output quality regressed or exposed
- "Write API test" is not a frontend bug — it is retrieved chunk metadata

## Spec conformance

| Doc | Result |
|-----|--------|
| F1, F2, F6 | In scope |
| `config-spec.md` | Extended with `VECINITA_MIN_RETRIEVAL_SCORE`, `VECINITA_CHAT_MAX_TOKENS` |
| `api-contract.md` | Modal `/generate` defaults unchanged; chat backend passes lower `max_tokens` |

**Blocking drift:** none.

## Repro test

| Test | Path | Status |
|------|------|--------|
| LLM repetition_penalty + retrieval threshold wiring | `tests/bugs/test_bug_2026_05_21_repetitive_assistant_answer.py` | red → green (user confirmed symptom match) |

## Verification plan

| Layer | Check | Status |
|-------|--------|--------|
| L1 | `pytest tests/bugs/…` + unit + integration chat_rag | **pass** |
| L2 | User re-ask on staging frontend | pending |
| L3 | `modal deploy` llm + DO ChatRAG redeploy | pending approval |
| L4 | Staging smoke after deploy | pending |

## TDD iteration log

| Run | Action | Result |
|-----|--------|--------|

## Fix

1. **`infra/modal/llm_app.py`**: `SamplingParams(repetition_penalty=1.15)` in `_generate_text`.
2. **`chat-rag-backend`**: `VECINITA_MIN_RETRIEVAL_SCORE` (default `0.2`) → retriever `score_threshold`; `VECINITA_CHAT_MAX_TOKENS` (default `256`); Qwen2.5 chat-format `_build_prompt`.
3. **`docs/config-spec.md`**: document new env vars.

## Timeline

| When | Event |
|------|--------|
| 2026-05-21 | Reported via 14-hotfix; intake batches A–C |
| 2026-05-22 | Phase 5 prevention interview; Cursor rule created |

## Interview record (Phase 5)

| Question | Answer |
|----------|--------|
| Recurrence risk | Very likely on model/prompt/corpus changes |
| Detect earlier | Multiple: unit tests, H3 staging smoke, golden questions |
| When / who | Now — with deploy PR |
| Cursor rule | Create now |

## Prevention & countermeasures

| Action | Status |
|--------|--------|
| `repetition_penalty`, `score_threshold`, chat template (fix) | **done** (local) |
| `test_bug_2026_05_21_repetitive_assistant_answer.py` | **done** |
| Cursor rule `.cursor/rules/chat-rag-llm-quality.mdc` | **done** |
| H3 staging golden-question smoke (non-repetitive answer) | **follow-up** after deploy |
| `docs/test-plan.md` golden fixture row | **follow-up** |

## Cursor rule

- **Path:** `.cursor/rules/chat-rag-llm-quality.mdc`
- **Declined:** no

## Follow-ups

- Deploy Modal LLM + DO ChatRAG (L3–L4); user L2 re-ask on staging frontend.
- Add TC/golden question asserting min source score and answer length cap.

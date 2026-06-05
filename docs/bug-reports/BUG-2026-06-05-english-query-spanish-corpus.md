# BUG-2026-06-05 — English query may not match Spanish-only corpus

> Status: **verifying** (L1 pass local; deploy pending)  
> GitHub: [#54](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/54)  
> Feature: **F1** (bilingual Q&A), **F22** (tag-aware retrieval)  
> Components: `packages/rag`, `apps/chat-rag-backend`, `apps/chat-rag-frontend` (EV-005 #57)

## Error description

On **staging**, users asking questions in **English** against a **Spanish-only** corpus receive wrong output — the bilingual no-context message ("I don't have enough community corpus context…") or poor retrieval — instead of a useful answer.

Issue intake (2026-05-30) states **correct behavior:** language toggle filters corpus **and** query language together (coordinate with EV-005 #57).

## Error logs

```
(none — user has no logs yet; exact query text TBD)
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Wrong output — no useful answer / "Vecina not known" style response |
| Where | Staging ChatRAG |
| When | After last deploy |
| Frequency | Every time — English question on Spanish-only corpus |
| Repro env | Staging only |
| Severity | Critical (user) |
| Evidence | None yet |
| Tried | Nothing |

## Remediation path

**deploy-live** — fix and deploy to staging/production ASAP (user 2026-06-05).

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Retriever does not filter `documents.language` — cross-lingual embedding mismatch | **Likely** — `CorpusPgvectorRetriever.retrieve_chunks` has tag filter only |
| H2 | `AskRequest` has no `language` field — UI cannot route corpus language | **Confirmed** — `chat_rag.py` has `question` + `tags` only |
| H3 | Auto-detect only affects no-context copy, not retrieval | **Confirmed** — `detect_query_language` used in `engine.py`, not `service.py` retrieval |
| H4 | EV-005 language toggle not shipped yet | **Open** — #57 related |

### Agent notes (pre-repro)

- Suggested branch: `fix/english-query-spanish-corpus`
- ADR-013 states retrieval is "language-agnostic on embeddings" — may conflict with issue intake; needs Step 1.5 spec cross-check

## Spec conformance

| Doc | Result |
|-----|--------|
| `ADR-013` | **Possible contradiction** — language-agnostic retrieval vs issue #54 language-filtered corpus |
| `openapi/chat-rag.yaml` | No `language` on `AskRequest` yet |
| `feature-list.md` F1, F22 | In scope |

**Blocking drift:** Resolved — ADR-013 amended for explicit `language` filter (EV-005).

## Repro test

| Test | Path | Status |
|------|------|--------|
| `test_ask_request_accepts_language_field` | `tests/bugs/test_bug_2026_06_05_english_query_spanish_corpus.py` | **green** (2026-06-05) |
| `test_retrieve_chunks_supports_language_filter` | same | **green** (2026-06-05) |
| `test_chat_service_passes_request_language_to_retriever` | same | **green** (2026-06-05) |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-05 | Added 3 repro tests | 3 failed (expected red) |
| 2 | 2026-06-05 | Language filter + UI toggle fix | 3 passed |

## Verification plan

| Field | Value |
|-------|--------|
| Success criterion | Original error gone — English query returns useful answer when EN corpus/language selected |
| Checks | Full main CI parity (local) + gh on main after merge |
| Post-deploy | 15-service-health follow-up |

| Layer | Check | Status |
|-------|--------|--------|
| L1 | pytest bugs + affected suites + ruff + basedpyright + frontend | **pass** |
| L2 | User repro on staging | pending |
| L3 | Staging query smoke H2/H3 | pending |
| L4 | Production/staging after deploy | pending |

## Root cause

**Code bug:** Retrieval had no `documents.language` filter; `AskRequest` lacked `language`; Chat UI hardcoded English tag facets. English queries on Spanish-only staging corpus missed relevant chunks (cross-lingual embedding + score threshold) → no-context answer.

## Fix

- `openapi/chat-rag.yaml` + `AskRequest.language` optional `en|es`
- `CorpusPgvectorRetriever.retrieve_chunks(..., language=)` SQL filter
- `ChatRagService._effective_language()` → retrieval + response language
- Chat UI: `useLocale` (localStorage, browser default→EN), `LanguageToggle`, tag chips by locale
- Corpus browse: same locale toggle + tag filter
- ADR-013 + `api-contract.md` updated

## Timeline

| When | Event |
|------|-------|
| 2026-06-05 | Hotfix intake started (issue #54) |

# ADR-013: Bilingual Q&A with automatic language detection

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

Vecinita targets **English and Spanish** community Q&A. The legacy worktree implemented bilingual prompts (en/es) in a LangGraph agent. The greenfield ChatRAG product retains bilingual scope (RD-002, RD-008) without porting LangGraph (ADR-006).

Operators may ingest corpus in either language; users should receive answers in the **same language as their question** without requiring a manual language toggle in v1.

## Decision

- **Supported languages (v1):** English (`en`), Spanish (`es`).
- **Detection:** Auto-detect query language on each request (library TBD in dependency inventory, e.g. `langdetect`).
- **Response:** Generate answer in the **detected query language**; include `language` field in JSON response (`docs/api-contract.md`).
- **Prompts:** LlamaIndex synthesis prompts in `packages/rag` respect detected language.
- **Corpus:** No requirement that corpus be single-language. When `AskRequest.language` is set (EV-005 UI toggle), retrieval filters `documents.language` to that value; when omitted, auto-detect from the question applies the same filter.
- **UI:** ChatRAG Frontend exposes an EN/ES toggle (`localStorage`); selected language is sent as `language` on ask/stream and filters tag chips.

### Out of scope v1

- More than en/es without new ADR.
- Automatic corpus translation.
- Per-user locale persistence (violates ADR-004).

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| User-selected language only | Worse UX; user chose auto-detect (RD-008) |
| Always English answers | Violates product intent |
| Separate indexes per language | Unnecessary with multilingual embeddings for v1 scale |

## Consequences

- Eval fixtures need en and es sample queries (`apps/database` seeds).
- Acceptance tests assert `language` matches question locale.
- Mis-detection is a quality issue — tune detector thresholds in config-spec, not schema changes.

## References

- RD-002, RD-008 (`docs/requirements-decisions.md`)
- feature-list F1 (`docs/feature-list.md`)
- `docs/api-contract.md` §POST `/api/v1/ask`
- ADR-004, ADR-006

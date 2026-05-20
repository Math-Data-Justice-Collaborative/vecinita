# ADR-006: LlamaIndex for RAG orchestration (not LangGraph)

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

ChatRAG Backend needs a retrieval-augmented generation pipeline: embed query, retrieve from pgvector, synthesize answer, optionally stream. The legacy worktree used **LangGraph** for agent orchestration. The 01-requirements interview selected **LlamaIndex** as the RAG framework (RD-005, RD-023).

LlamaIndex fits a **stateless, single-request Q&A** model (ADR-004). LangGraph excels at multi-step agents with checkpoints — patterns that conflict with zero personal data and no server-side session history.

## Decision

- Implement RAG in **`packages/rag`** using **LlamaIndex** (core runtime dependency).
- **ChatRAG Backend** (`apps/chat-rag-backend`) invokes `packages/rag`; no LangGraph in v1.
- Integrations: pgvector retriever (Postgres on DO), HTTP clients to Modal FastEmbed and LLM (ADR-008, ADR-009).
- **Not using:** LangGraph, persistent LangGraph checkpoints, or identity-keyed agent state.

### Responsibilities

| Layer | Responsibility |
|-------|----------------|
| `packages/rag` | VectorStoreIndex / query engine, synthesis, source node metadata |
| ChatRAG Backend | HTTP routes, validation, language detect, Modal HTTP calls |
| Modal | Embedding and generation only — not orchestration |

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| LangGraph (worktree) | Checkpoint/session patterns; user chose LlamaIndex |
| Custom pipeline only | Reinvents retriever/synthesizer; LlamaIndex is MIT and fits scope |
| RAG logic entirely on Modal | Couples orchestration to GPU tier; DO API should own query path |

## Consequences

- `llama-index` and pgvector adapter versions pinned in `pyproject.toml` during 06-tech-tooling.
- Dependency weight and version lockstep with `llama-index-vector-stores-postgres` — track in dependency inventory.
- Tests mock LlamaIndex boundaries in `packages/rag` for unit coverage.
- Agent-style multi-tool workflows deferred unless a future ADR extends scope.

## References

- RD-005, RD-023 (`docs/requirements-decisions.md`)
- feature-list F4 (`docs/feature-list.md`)
- `docs/dependency-inventory.md` §LlamaIndex evaluation
- ADR-004 (stateless chat), ADR-007 (Postgres read on DO)

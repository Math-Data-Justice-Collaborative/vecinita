# ADR-009: vLLM as primary LLM on Modal

**Status:** Accepted  
**Stage:** 01-requirements (deployment batch)  
**Date:** 2026-05-19

## Context

ChatRAG needs **self-hosted text generation** on Modal (ADR-002, ADR-004). Early requirements documented **Ollama vs vLLM** as an open choice for `04-tech-plan` (RD-006). Sibling `vecinita-model` used **Ollama** on a Modal volume.

The deployment integration batch selected **vLLM as primary** (RD-021) for higher throughput on GPU. This trades **higher Modal GPU cost** against ADR-004 budget targets — `04-tech-plan` must size model and GPU tier or raise `[Decision]`.

## Decision

- **Primary LLM runtime:** **vLLM** on Modal (`vecinita-llm` app).
- **ChatRAG Backend** calls Modal LLM via HTTP (credentials on DO; never in browser).
- **Ollama:** Documented **fallback/alternate** if cost proof fails — switching requires spec update and cost re-estimate, not silent drift.
- **No default** paid SaaS LLM APIs (OpenAI, Anthropic, etc.) — ADR-004.

### Interface (summary)

- Routes aligned with sibling pattern: health, chat/completion, stream (exact paths in `docs/api-contract.md` and OpenAPI).
- Streaming consumed by `POST /api/v1/ask/stream` on ChatRAG Backend.

## Alternatives considered

| Alternative | Why rejected as default |
|-------------|-------------------------|
| Ollama on Modal (siblings) | User selected vLLM primary in deployment batch |
| LLM on DO CPU | Insufficient for community RAG latency/quality at scale |
| Third-party APIs | Cost, sovereignty, data leakage — ADR-004 |
| LlamaIndex-only local LLM on DO | GPU not on DO tier; Modal hosts GPU |

## Consequences

- **Cost risk R1:** vLLM GPU minutes + multi-app DO may exceed $25/mo target — mandatory estimate in `04-tech-plan`.
- Separate Modal app lifecycle from embedding and ingest.
- **Model card:** `Qwen2.5-1.5B-Instruct` (04-tech-plan TP-002).
- **GPU:** Modal NVIDIA **T4**, scale-to-zero (04-tech-plan).
- Pins in dependency inventory and deploy docs at tasks T9.2 / T8.1.
- Cold start latency excluded from p95 < 15s target (RD-017) but must be documented for ops.

## References

- RD-006, RD-021 (`docs/decisions.md#requirements-decisions-01-requirements`)
- `docs/deployment-integration.md` §Services
- `docs/dependency-inventory.md` §vLLM evaluation
- `docs/sessions/S000-internal-docs-archive/reference.md#risk-register` R1
- ADR-002, ADR-004, ADR-006

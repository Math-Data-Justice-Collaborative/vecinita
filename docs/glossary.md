# Glossary

> **Project**: Vecinita  
> **Last updated**: 2026-06-13 (EV-004 F31)

| Term | Definition | Context |
|------|------------|---------|
| **ChatRAG** | Bilingual community Q&A product (chat UI + RAG backend) | apps/chat-rag-* |
| **Corpus** | Collection of public documents ingested for retrieval | Postgres documents/chunks |
| **Chunk** | Text segment of a document used for embedding and retrieval | `chunks` table |
| **Embedding** | 384-dimensional vector from FastEmbed | `embeddings` table |
| **pgvector** | Postgres extension for vector similarity search | Database app |
| **Modal** | Serverless GPU/CPU platform for workers and vLLM | ADR-002 |
| **DO internal write API** | DO-hosted API sole holder of DATABASE_URL for writes | ADR-007 |
| **Job** | Async ingest unit (URLs → scrape → embed → store) | `/jobs` API |
| **LlamaIndex** | RAG orchestration library (retriever + synthesizer) | packages/rag |
| **vLLM** | Primary LLM inference server on Modal (v1) | vecinita-llm app |
| **Zero personal data** | No PII for visitors or operators in Vecinita DB | ADR-004 |
| **Stateless chat** | No server-side conversation history across requests | F3 |
| **Infrastructure auth** | API keys / private network — not app user accounts | F16 |
| **UJ-ID** | User journey identifier for E2E mapping | user-journeys.md |
| **E2E tier** | `local` (v1) or `live` (post-deploy) | test-plan |
| **Tag** | Metadata label on a document or chunk for browse and RAG filter | F19–F22; `tags` table |
| **Tag slug** | Normalized machine identifier for a tag (facet filter, API) | config-spec |
| **Tag source** | Provenance `llm` or `human` — no operator identity | ADR-014, ADR-004 |
| **Seed tag vocabulary** | Starter tag list loaded from `data/fixtures/tags/seed_tags.json` | F20, RD-031 |
| **Corpus browse** | Public paginated document discovery in ChatRAG frontend | F19, UJ-009 |
| **UI locale** | Browser UI language (`en` \| `es`) stored in `localStorage` key `vecinita.locale` | F31, ADR-019 |
| **UI chrome** | Static frontend labels (nav, buttons, empty states) — distinct from corpus content language | F31, R30 |
| **frontend-i18n** | Workspace package `vecinita-frontend-i18n` — locale detection + message tables | F31 |
| **frontend-ui** | Workspace package `vecinita-frontend-ui` — shared React bilingual UI components | F31, ADR-020 |

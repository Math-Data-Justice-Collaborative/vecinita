# Glossary

> **Project**: Vecinita  
> **Last updated**: 2026-05-19

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

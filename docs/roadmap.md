# Roadmap

> **Project**: Vecinita  
> **Last updated**: 2026-05-19

## Vision

Deliver a **cost-conscious, US-hosted, zero-PII** bilingual community Q&A platform with operator-controlled corpus ingest — five deployable apps in one monorepo, hybrid Modal + DigitalOcean.

## Phases

### Phase 1: Foundation (Database + packages)

- [ ] Monorepo scaffold (`apps/*`, `packages/*`)
- [ ] Alembic + pgvector schema + privacy tests
- [ ] Seed fixtures (EN/ES)
- [ ] OpenAPI skeletons

### Phase 2: Data Management (Modal + DO write API)

- [ ] DO internal write API
- [ ] Modal ASGI `/jobs` + ingest workers
- [ ] FastEmbed Modal app
- [ ] Data Management Frontend (jobs UI)
- [ ] UJ-002, UJ-006, UJ-008 E2E

### Phase 3: ChatRAG (LlamaIndex + vLLM)

- [ ] `packages/rag` LlamaIndex integration
- [ ] ChatRAG Backend `/ask` + stream
- [ ] vLLM Modal app
- [ ] ChatRAG Frontend
- [ ] UJ-001, UJ-005 E2E

### Phase 4: Integration & deploy

- [ ] docker-compose + Modal serve docs (UJ-004)
- [ ] GitHub Actions CI
- [ ] Staging deploy DO + Modal
- [ ] Cost estimate ≤ $50/mo validation
- [ ] 11-verify-impl + 13-deploy-smoke

### Phase 5: Post-v1 (deferred)

- [ ] Dedicated API gateway (R6)
- [ ] Multimodal / PDF ingest
- [ ] Model fine-tuning
- [ ] Live staging E2E tier
- [ ] Advanced admin analytics

## Non-goals

- User/admin accounts in application DB
- RFantibody / protein design
- Multi-region deployment
- Paid third-party LLM as default

## Open questions

- Reach **$25/mo target** — may require DO consolidation after pilot metrics
- Exact dependency pins during 07-build (T8.1, T9.2)

**Resolved in 04-tech-plan:** cost pilot ≤ $50; gateway deferred; vLLM Qwen2.5-1.5B on T4.

# Roadmap

> **Project**: Vecinita  
> **Last updated**: 2026-06-13 (EV-004 F31)

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

### Phase 5: EV-001 — Corpus tags & browse (complete)

**Merged:** PR-24 → `main` (2026-05-24)  
**ADR:** ADR-014 (product), ADR-015 (technical)

- [x] M15: Tag schema + fixtures (D8, D9 verified)
- [x] M16: LLM auto-tag at ingest + admin re-tag job (F20)
- [x] M17: Public browse API, `/corpus` UI, tag-filtered RAG (F19, F22)
- [x] M18: Admin chunk viewer & tag editor (F21)
- [x] M19: Staging connectivity smoke scripts (TC-046, TC-049; live H4/H5 operator-run)
- [x] UJ-009–UJ-012 E2E (local tier)

### Phase 6: Post-v1 (deferred)

- [ ] Dedicated API gateway (R6)
- [ ] Multimodal / PDF ingest
- [ ] Model fine-tuning
- [ ] Live staging E2E tier
- [ ] Advanced admin analytics

### Phase 7: EV-004 — Admin bilingual UI + shared frontend packages (in progress)

**Cycle:** EV-004  
**ADR:** ADR-019 (frontend-i18n), ADR-020 (frontend-ui)

- [ ] F31: `packages/frontend-i18n` + `packages/frontend-ui` workspace packages
- [ ] F31: Admin dashboard full en/es UI chrome (~120+ strings)
- [ ] F31: ChatRAG migration to shared packages + full Tailwind layout
- [ ] F31: Root npm workspaces + CI package build order
- [ ] UJ-022 Vitest coverage (TC-065–TC-069)
- [ ] Deploy both static frontends (no backend redeploy)

## Non-goals

- User/admin accounts in application DB
- RFantibody / protein design
- Multi-region deployment
- Paid third-party LLM as default

## Open questions

- Reach **$25/mo target** — may require DO consolidation after pilot metrics
- Exact dependency pins during 07-build (T8.1, T9.2)

**Resolved in 04-tech-plan:** cost pilot ≤ $50; gateway deferred; vLLM Qwen2.5-1.5B on T4.

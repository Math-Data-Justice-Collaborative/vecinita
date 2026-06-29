# Reference

Consolidated roadmap, glossary, risk register, and cost monitoring docs.

## Roadmap

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

## Glossary

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

## Risk register

> **Project**: Vecinita  
> **Last updated**: 2026-06-13 (EV-004 F31)

| # | Risk | Likelihood | Impact | Mitigation | Status |
|---|------|------------|--------|------------|--------|
| R1 | Monthly cost exceeds **$50** (multi-app DO + vLLM GPU) | Medium | High | Line-item in execution-plan; consolidate DO first; Ollama fallback | Mitigated (pilot est. ≤ $50) |
| R2 | Stale RFantibody `.cursor/rules/` mislead build agents | Low | Medium | 03-plan-tooling rewrite (ISS-001) | Resolved |
| R3 | Sibling API drift if ports copied without OpenAPI | Medium | Medium | OpenAPI-first; greenfield contracts | Mitigated |
| R4 | Accidental PII table in migration | Medium | High | Privacy tests + CI deny-list | Mitigated |
| R5 | vLLM cold start breaks p95 < 15s | Medium | Medium | Warm pools; smaller model; measure in smoke | Open |
| R6 | Modal worker cannot reach DO internal API | Low | High | Private networking / stable TLS; integration tests | Open |
| R7 | Third-party LLM introduced by dependency | Low | High | Dependency audit; ADR for exceptions | Open |
| R8 | LlamaIndex version incompatibility with pgvector | Medium | Medium | Pin versions; integration tests | Open |
| R9 | Multi-app DO secrets sprawl | Medium | Low | Document secret matrix in deploy plan | Open |
| R10 | LLM tagging increases ingest cost/latency | Medium | Medium | Cap tags; batch tag step; monitor Modal spend | Open (EV-001) |
| R11 | Admin corpus API key in static frontend bundle | Medium | High | BFF/server proxy in 04-tech-plan; rotate keys | Open (EV-001) |
| R12 | Shared frontend package CI drift (workspace link breaks app build) | Medium | Medium | Root npm workspaces; CI builds packages before frontend matrix; pin workspace versions | Open (EV-004) |
| R13 | ChatRAG Tailwind migration regressions during F31 | Medium | Medium | Vitest component tests; visual snapshot on key pages; incremental migration | Open (EV-004) |
| R14 | i18n string drift between admin and ChatRAG | Low | Medium | Single `frontend-i18n` source; typed message keys; TC-066/069 | Mitigated (EV-004 design) |

## Risk details

### R1: Cost overrun

- **Description:** User chose **multi-app DO topology** and **vLLM as primary LLM** — both increase spend vs ADR-004 $25 target.
- **Trigger:** Deploy to production without cost spreadsheet.
- **Mitigation:** 04-tech-plan must prove ≤ $50 or `[Decision]` to change topology/model.
- **Owner:** ⚠️ User + tech plan stage

### R2: Stale Cursor rules

- **Description:** `.cursor/rules/` reference RFantibody Modal job template.
- **Trigger:** 07-build agent follows wrong constraints.
- **Mitigation:** 03-plan-tooling before 07-build.
- **Source:** ISS-001

### R4: PII schema regression

- **Description:** Future migration adds `users` or `messages`.
- **Trigger:** Feature creep / ported sibling code.
- **Mitigation:** `tests/privacy/test_no_pii_tables.py` blocking in CI.
- **Source:** ADR-004

## Cost monitoring baseline (ADR-004)

> **Cap:** ≤ **$50/mo** hard limit · **Target:** ≤ **$25/mo** preferred  
> **Source:** `#risk-register` R1, `docs/execution-plan.md` §Cost Estimate (T14.4)

## Pilot line items (2026-05-19)

| Resource | Est. $/mo | Notes |
|----------|-----------|-------|
| DO Managed Postgres (1 GB) | ~15 | Basic tier, single region `nyc` |
| DO App Platform (4 apps) | ~20–27 | basic-xxs web + static sites |
| Modal CPU (embed + scrape) | ~2–8 | Per invoke, scale-to-zero |
| Modal GPU T4 (vLLM) | ~5–20 | Scale-to-zero; cold starts |

**Pilot total:** ~**$42–48/mo** (within cap if GPU not 24×7).

## Alert thresholds

| Threshold | % of $50 cap | Action |
|-----------|--------------|--------|
| **Watch** | 80% ($40) | Review DO component sizes; confirm Modal scaledown |
| **Cap** | 100% ($50) | Stop non-essential GPU; consolidate DO apps per execution-plan interview |

## Monthly checklist

1. DO billing → sum App Platform + Managed Database.  
2. Modal workspace → GPU hours + CPU container hours.  
3. Compare to table above; if over **$40**, apply mitigations:
   - Merge static sites into one DO static app (future ADR).  
   - Reduce vLLM `scaledown_window` / use smaller model.  
   - Pause staging when not in use.  
4. Record actuals in deploy retrospective (skill 13-deploy-smoke).

## Consolidation triggers

Raise `[Decision]` to consolidate DO topology if:

- Two consecutive months > **$50**, or  
- Staging-only spend > **$40** without production traffic.

See ADR-010 alternatives and execution-plan §Cost consolidation interview.

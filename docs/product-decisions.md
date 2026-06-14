# Product decisions log (02-verify-plan)

> **Stage**: 02-verify-plan  
> **Last updated**: 2026-06-13 (EV-004 F31 delta)

Chronological verdicts from product plan verification. Auto-approved entries trace to
`docs/requirements-decisions.md` (interview).

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-19 | S1.1–S1.18 | auto-approved | Features F1–F18 scope from interview (RD-002–RD-011, RD-014) |
| 2026-05-19 | S2.1–S2.12 | auto-approved | Core architecture/constraints from interview + ADRs |
| 2026-05-19 | S3.1–S3.8 | auto-approved | UJ-001–UJ-008 from feature-list mapping |
| 2026-05-19 | S4.1–S4.6 | auto-approved | Test plan UJ/TC mapping from journeys |
| 2026-05-19 | S5.1–S5.4 | auto-approved | Config env vars from interview defaults |
| 2026-05-19 | S6.1–S6.3 | auto-approved | API routes from RD-018, RD-019 |
| 2026-05-19 | S7.1–S7.4 | auto-approved | Acceptance criteria mirror test-plan |
| 2026-05-19 | S8.1–S8.3 | auto-approved | Deployment hybrid + vLLM primary (RD-021, RD-022) |
| 2026-05-19 | S9.1–S9.2 | auto-approved | Data fixtures schema from interview |
| 2026-05-19 | S10.1–S10.2 | auto-approved | LlamaIndex + vLLM deps from RD-005, RD-021 |
| 2026-05-19 | S11.1 | auto-approved | Roadmap phases align with feature-list |
| 2026-05-19 | S12.1 | auto-approved | Glossary terms from ADRs |
| 2026-05-19 | S13.1–S13.2 | auto-approved | Risk R1/R2 from workflow issue_log |

| 2026-05-19 | S-C1 | modified | `VECINITA_LLM_BACKEND` default → `vllm`; spec overview aligned |
| 2026-05-19 | S-C2 | modified | feature-list F6 → vLLM primary, Ollama fallback |
| 2026-05-19 | S-C3 | modified | spec diagram/overview → vLLM primary (with S-C1) |
| 2026-05-19 | S-C4 | modified | ADR-001 chat-rag-backend → LlamaIndex + correct routes |
| 2026-05-19 | S8.4 | approved | DO internal write API = standalone App Platform service |
| 2026-05-19 | S1.19 | approved | No API gateway in v1; direct backend URLs |

| 2026-05-19 | S1.13 | approved | F14 seed corpus & eval fixtures in v1 |
| 2026-05-19 | S1.14 | approved | Server-side chat history forbidden |
| 2026-05-19 | S6.3 | approved | SSE events: token, sources, done |
| 2026-05-19 | S7.2 | approved | ≥80% manual retrieval relevance on eval fixture |
| 2026-05-19 | S4.3 | approved | GitHub Actions PR CI (YAML in 06-tech-tooling) |

| 2026-05-19 | S6.2 | approved | Internal write API prefix `/internal/v1` |
| 2026-05-19 | S5.5 | modified | Add `vecinita.yaml` for v1 local/staging defaults |
| 2026-05-19 | S4.4 | approved | p95 latency informative in v1 CI, not blocking |
| 2026-05-19 | S9.2 | modified | Production may include seed/eval fixtures |
| 2026-05-19 | S13.3 | approved | Risk R5 (vLLM cold start) open with mitigations |
| 2026-05-19 | S2.14 | approved | Standalone internal write API (via S8.4) |
| 2026-05-19 | S8.3 | approved | 04-tech-plan must prove ≤ $50/mo cost |
| 2026-05-19 | S9.1 | approved | HF model weights on Modal volumes |
| 2026-05-19 | S11.2 | approved | Staging deploy before live E2E (10-e2e) |
| 2026-05-19 | S5.6 | approved | Optional strict mode for unknown env vars |
| 2026-05-19 | S10.3 | approved | vLLM GPU sizing deferred to 04-tech-plan |
| 2026-05-19 | S12.2 | approved | Modal apps in US workspace |

| 2026-05-19 | D1–D4 | auto-fixed | Partial re-run: F14/TBD params, deploy checklist, ADR-001 invites, RD-006 note |

## EV-001 delta (2026-05-24)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-24 | S-EV1.1–S-EV1.14 | auto-approved | F19–F22 scope from RD-024–RD-033 / ADR-014 |
| 2026-05-24 | S-EV1.C1 | modified | Added TC-047 ingest LLM auto-tag; AC-T3 → TC-047 |
| 2026-05-24 | S-EV1.C2 | approved | test-plan E2E local scope → UJ-001–012 |
| 2026-05-24 | S-EV1.15 | approved | VITE admin corpus API key acceptable v1; ADR-014 noted |

## EV-002 delta (2026-05-26)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-26 | S-EV2.1–S-EV2.14 | auto-approved | F23–F29 scope from RD-034–RD-052 / ADR-016 |
| 2026-05-26 | S-EV2.C1 | approved | ADR-016 stands: no IP stored, request_id only (user approved) |
| 2026-05-26 | S-EV2.15 | approved | 9 new endpoints on internal-write-api, /internal/v1/ paths |
| 2026-05-26 | S-EV2.16 | approved | Bulk delete: hard-delete, max 100, audit record preserved |
| 2026-05-26 | S-EV2.17 | approved | Serving stats: new table, async fire-and-forget, dashboard-only |
| 2026-05-26 | S-EV2.18 | approved | Health: manual refresh, frontend-direct, Postgres proxied |
| 2026-05-26 | S-EV2.19 | approved | CORS on all new EV-002 endpoints from admin frontend origin |
| 2026-05-26 | S-EV2.20 | approved | 3 new tables in allow-list; privacy tests updated |
| 2026-05-26 | S-EV2.21 | approved | New VITE_VECINITA_*_HEALTH_URL env vars + timeout default 5000ms |
| 2026-05-26 | S-EV2.22 | added | AC-E1–AC-E11 acceptance criteria for F23–F29 |
| 2026-05-26 | S-EV2.23 | modified | UJ-020 (F23 admin UI) + UJ-021 (F24 tag display) added per user request |

## EV-004 delta (2026-06-13)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-06-13 | S-EV4.1–S-EV4.15 | auto-approved | F31 scope from RD-053–RD-066 / ADR-019, ADR-020 |
| 2026-06-13 | S-EV4.M1 | approved | ~120+ admin static strings scope |
| 2026-06-13 | S-EV4.M2 | approved | Full ChatRAG Tailwind migration in EV-004 |
| 2026-06-13 | S-EV4.M3 | approved | Typed i18n keys + runtime dev fallback |
| 2026-06-13 | S-EV4.C1 | fixed | Feature matrix: added F30, F31 rows |
| 2026-06-13 | S-EV4.C2 | fixed | Journey index + test-plan E2E table: UJ-020, UJ-021 |
| 2026-06-13 | S-EV4.C3 | approved | H4/H5 regression at deploy — AC-F7 added |
| 2026-06-13 | S-EV4.L1 | approved | Non-en/es browser default → ES |
| 2026-06-13 | S-EV4.L2 | denied | ThemeToggle extracted to `frontend-ui` — RD-067 |

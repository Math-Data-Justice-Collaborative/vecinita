# RET-002 — Evidence digest (internal)

> **Cycle:** RET-002 · **Session:** S027-multilingual-embeddings  
> **Window:** after RET-001 (2026-08-02) → 2026-08-06  
> **Scope:** evolve_hotfix · **Depth:** standard · **Transcripts:** full in window  
> **Status:** Phase 1–2 complete (hypotheses; validate in Phase 3)

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/decisions/evolve-decisions.md §Cycle EV-025]  
[Spec: docs/archive/evolve-history.md §EV-025]

## Intake

| Field | Choice |
|-------|--------|
| Scope | Evolve + hotfix (supporting 07–13) |
| Time window | Since last retro (RET-001) |
| Depth | Standard |
| Transcripts | Full available in window |

## Evidence digest

**Transcript mining:** parent dirs after 2026-08-02 ≈ **94**; parent `*.jsonl` ≈ **88**; deep-sampled **16** evolve/hotfix-heavy parents. Sample aggregates: AskQuestion≈179 · `[Decision]`≈70 · markdown “Reply `1`…” fallback in **7/16**.

### Sessions reviewed (sample)

| Short title | UUID |
|-------------|------|
| [RET-002 intake / 16-evolve Continue](2dd4db63-542f-463c-847c-ed351c2ce6e3) | `2dd4db63-…` |
| [S027 F71 staging promote → close](e61c0493-43a9-4f27-8ad9-b1e727c99dc9) | `e61c0493-…` |
| [14-hotfix continue after #220](5c0f4477-3892-4d43-b657-f336610ffdea) | `5c0f4477-…` |
| [S027 QA advisories then cutover](25c1ed29-b97b-416f-92d7-6e12f2dadef7) | `25c1ed29-…` |
| [S027 M121 / PR #211](97aaf011-be21-4ab5-be96-119565c6f94c) | `97aaf011-…` |
| [S027 waive compose e2e](1c97e951-c5f4-44fd-aed6-cffa51fd2fe9) | `1c97e951-…` |
| [S027 T120.5 Docker gate](828d8a64-4e67-4acf-9618-2986fe356355) | `828d8a64-…` |
| [S027 CI policy D34](a6856072-2de1-42c9-98ed-d785a905f2fe) | `a6856072-…` |
| [S027 Gate B→C M119](d3b461e1-150c-4045-9c34-016273d5b203) | `d3b461e1-…` |
| [S027 continue recommended](6d3988bb-7a77-4aa3-82c7-6ad5141f5597) | `6d3988bb-…` |
| [S027 start #159 multilingual](f2ca0d2f-0224-4de6-a086-31c10aacffe1) | `f2ca0d2f-…` |
| [S026/EV-024 12-verify-deploy](0f01402f-cdea-47e8-b2f0-af8008f44aef) | `0f01402f-…` |
| [S026 merge through M117](7587c8af-c407-4527-8b23-e8ca7c515932) | `7587c8af-…` |
| [S026 M113 after #200](4be3b519-9909-4b58-9867-aa274be607cb) | `4be3b519-…` |
| [S026 Batch B lock F64–F69](da335c82-98f1-4aad-b917-cee5abd1440a) | `da335c82-…` |
| [no-live-prod-corpus rule](bd4eb71d-5fb1-40a2-bdac-eb83678b3606) | `bd4eb71d-…` |

### Cycles in window

| Cycle | Session | One-liner |
|-------|---------|-----------|
| EV-019 | S022 | Ingest resilience; Path B rechunk waived |
| EV-020 | S023 | Retrieval top_k packing; Path A PASS |
| EV-022 | S024 | Website scrape/crawl; local Docker waived |
| EV-023 | S025 | CI/release F62–F63; `v0.4.1` |
| EV-024 | S026 | Frontend UX F64–F69 multi-PR train |
| EV-025 | S027 | Multilingual F70–F71; #221; staging-as-live; 15 PASS |

### Stages touched

**Primary:** 16-evolve, 14-hotfix, 15-service-health, pipeline  
**Supporting:** 07–13 (heavy on S026–S027)

### Recurring patterns

1. **Cycle velocity** — ~6 evolve cycles in ~4 days; long Continue threads.
2. **Hotfix mid-evolve** — #220 ChatRAG health + #221 FastEmbed→ST during F71 cutover.
3. **Compose/Docker waive class** — S021 → S024-D41 → S027-D35; Gate C→D often conditional.
4. **CI policy pivot (S027-D34)** — remote unit+coverage; compose local.
5. **Staging-as-live (S027-D60/D61)** — no distinct prod DO stack; staging promote = live.
6. **Flaky security install** — S027-D41 / issue `S027-FLAKY-SECURITY-INSTALL`.
7. **AskQuestion markdown fallback** — still common when MCP AskQuestion unavailable (RET-001 theme persists).
8. **Spec→ops gap** — S027-D12 ST fallback approved but not shipped before E1 pin hit FastEmbed.
9. **Corpus safety** — BUG-2026-08-02 + `no-live-prod-corpus-push` rule.
10. **Merge-gate churn** — CI green → wait on explicit merge/promote AskQuestion.

### issue_log / hotfix themes

| Theme | Class | Evidence |
|-------|-------|----------|
| E1 FastEmbed unsupported → H3 hang | code + ops | BUG-2026-08-05; #221 |
| ChatRAG ask blocks /health | code | PR #220 |
| Staging corpus wipe | tooling/code | BUG-2026-08-02 |
| Docker userns / compose | tooling | S027-D32/D35 |
| CI remote vs local | tooling/spec | S027-D34 |
| Prod = staging-as-live | spec/ops | S027-D60/D61 |
| Flaky security-install | tooling | S027-D41 |
| AskQuestion MCP → markdown | tooling | 7/16 sample; RET-001 |

### Spec vs code vs tooling (approx)

| Class | Count |
|-------|------:|
| Spec / decision / env model | 4 |
| Code / product defect | 3 |
| Tooling / agent host / CI | 5 |

## Skill rubric (Phase 2) — hypotheses only

| Stage | Skill worked? | Evidence | Hypothesis | Confidence |
|-------|---------------|----------|------------|------------|
| **16-evolve** | Partially | 6 cycles/4d; D34/D35/D60–D63; mid-cycle hotfixes | Continues well; under-gates “prod bug → pause 16 / enter 14”; conditional waives accumulate | high |
| **14-hotfix** | Yes (reactive) | #220/#221; ops-then-code D55 | Recovered prod; mid-evolve interrupt entry is ad hoc | high |
| **15-service-health** | Yes late | D62 15-before-close; H3 caught E1 | H3 effective; health≠embed-ready gap needs callout | medium |
| **pipeline** | Partially | Continue chains; markdown fallback | Resume works; AskQuestion tool gap thrash | medium |
| **07-build** | Mostly | M112–M122 PR train | Strong rhythm; over-reliance on remote CI when Docker down | medium |
| **08-verify-build** | Conditionally | PASS cond. D35 | Conditional PASS may be overused | medium |
| **12-verify-deploy** | Friction | D60 Ambiguity | Assumes distinct staging vs prod | high |
| **13-deploy-smoke** | Conditionally | D61; H3 mid-path | Finds real bugs; “what is live” unclear | high |

## Open questions (Phase 3+)

1. Mid-evolve hotfix vs hard pause 16 when H3 fails?
2. Make S027-D34 standing CI doctrine?
3. Confirm staging-as-live as lasting prod model?
4. Compose waive indefinitely vs Docker recovery P1?
5. Earlier ST fallback / runtime validation in 07?
6. Security-install flake: rerun / pin / soft-fail?
7. AskQuestion MCP fix vs formalize markdown fallback?
8. Cool-down / mandatory 17 between evolve bursts?

<!--
Sync Impact Report
- Version change: (unversioned template placeholders) → 1.0.0
- Principles: Initial adoption (replaced five placeholder principles with Vecinita-specific principles)
- Added sections: Community RAG & corpus mission; Domain requirements & ethics; Engineering workflow
- Removed sections: None (template scaffolding replaced, not deleted)
- Templates: .specify/templates/plan-template.md ✅ Constitution Check gates updated;
  .specify/templates/spec-template.md ✅ Requirements preamble references constitution;
  .specify/templates/tasks-template.md ✅ Task generation bullet references constitution
- Follow-up: None
-->

# Vecinita Constitution

## Core Principles

### I. Community benefit and public corpus

Vecinita MUST be designed as a **chatbot and data-management system** for **RAG over a corpus of
public documents** in service of **community good** (e.g., housing, civic, and neighborhood
information). Features MUST default to outcomes that improve **access**, **clarity**, and **fair
use** of public knowledge—not extraction of value from vulnerable users. Product and technical
decisions that trade community benefit for convenience MUST be documented and consciously
approved.

### II. Trustworthy retrieval and attribution

Answers and APIs that surface retrieved content MUST preserve **traceability to sources**:
citations, links, or metadata that allow users and operators to verify claims against the corpus.
The system MUST NOT present generated text as authoritative fact without grounding in retrievable
evidence when the feature is retrieval-backed. Limits of the corpus (stale data, gaps, language
coverage) MUST be representable in UX or API contracts where user harm from overconfidence is
material.

### III. Data stewardship and responsible ingestion

Ingestion, scraping, reindexing, and data-management flows MUST respect **robots/licensing**,
**rate limits**, and **documented data-retention** policies. PII and non-public sensitive data MUST
NOT enter the public corpus without an explicit, reviewed policy path. Operators MUST be able to
audit what was ingested, when, and from where (job IDs, logs, or equivalent). Bilingual
(English/Spanish) and accessibility expectations from product goals MUST be treated as first-class
constraints when they affect UX or content.

### IV. Safety, quality, and verifiable delivery

Guardrails, validation, and **automated tests** appropriate to risk class MUST accompany changes to
the agent, gateway contracts, and ingestion pipelines. Breaking changes to stable client surfaces
(e.g., versioned HTTP APIs) MUST follow migration or compatibility discipline. **Local CI**
(`make ci` or documented equivalent) MUST pass before work is declared merge-ready unless an
explicit, documented exception applies.

### V. Operational simplicity and service boundaries

The monorepo’s **gateway / agent / embedding / scraper / frontend** boundaries MUST be respected:
new coupling crosses a service boundary only with clear contracts (OpenAPI, shared schemas, or
documented events). Prefer small, reversible changes over speculative abstraction. Observability
(structured logs, health endpoints, trace-friendly IDs) MUST be sufficient to debug production
issues without redeploying ad-hoc instrumentation for routine failures.

## Domain requirements and ethics

- **Public-good scope**: Specifications SHOULD name the community or domain context (e.g., public
  housing resources) when it affects acceptance criteria or compliance.
- **Corpus integrity**: Plans and tasks for ingestion MUST include validation of source lists,
  deduplication, and error handling for failed loads.
- **Equity**: Language, literacy, and device constraints SHOULD appear in user scenarios when the
  feature touches end users.

## Engineering workflow and quality gates

- **Specs and plans**: Feature work uses `.specify/templates/` artifacts; plans MUST include a
  **Constitution Check** gate before Phase 0 and re-check after Phase 1 design.
- **Testing**: Contract and integration tests MUST cover gateway OpenAPI surfaces and cross-service
  assumptions touched by the feature; follow `TESTING_DOCUMENTATION.md` for Schemathesis and live
  test norms.
- **Reviews**: PRs MUST confirm constitution principles relevant to the change (mission, trust,
  data, safety, boundaries) are satisfied or explicitly deferred with rationale.

## Governance

This constitution **supersedes** informal ad-hoc practices for Specify-driven feature work when
they conflict. **Amendments** require: (1) an updated `.specify/memory/constitution.md` with version
bump and Sync Impact Report; (2) alignment of dependent templates or docs listed in the report;
(3) team or maintainer review as per repository contribution rules. **Versioning**: semantic
versioning—**MAJOR** for incompatible principle removals or redefinitions; **MINOR** for new
principles or materially expanded obligations; **PATCH** for clarifications only.
**Compliance**: Spec authors and implementers MUST verify gates at plan and task boundaries;
reviewers SHOULD block merges that violate a MUST without documented exception.

**Version**: 1.0.0 | **Ratified**: 2026-04-18 | **Last Amended**: 2026-04-18

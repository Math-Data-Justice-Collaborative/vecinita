# Implementation Plan: Chat Message Presentation

**Branch**: `007-chat-message-presentation` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/006-chat-message-presentation/spec.md`

## Summary

Improve chat UX by transforming assistant payloads into safe, readable markdown-rendered messages with consistent visual hierarchy, table overflow handling, and explicit image/HTML safety rules. Implementation will prefer existing TypeScript libraries already present in the frontend stack and use Playwright for E2E validation of rendering behavior.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), existing React/Vite app conventions  
**Primary Dependencies**: Existing markdown/rendering stack in `frontend` (reuse current TS libs first), Playwright (`@playwright/test`) for E2E, existing unit test tooling  
**Storage**: N/A (presentation-only feature)  
**Testing**: Unit/component tests for parser/renderer behavior + Playwright E2E scenarios for end-user rendering outcomes  
**Target Platform**: Web SPA in modern desktop/mobile browsers  
**Project Type**: Web application (frontend-focused, no backend contract changes)  
**Performance Goals**: No perceptible chat render delay regression; long markdown messages remain interactive and readable  
**Constraints**: No raw payload object rendering in chat body; no inline remote image loading; raw HTML must be stripped/escaped  
**Scale/Scope**: Existing chat interface in `frontend`; rendering rules applied to all assistant messages in-session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design. Source:
`.specify/memory/constitution.md`.*

- **Community benefit**: **Pass** - clearer agent responses improve accessibility to public-information guidance.
- **Trustworthy retrieval**: **Pass** - presentation changes preserve readable grounded output without altering retrieval semantics.
- **Data stewardship**: **Pass** - no new ingestion/storage; remote media loading is constrained by design.
- **Safety & quality**: **Pass** - markdown safety, HTML stripping, and Playwright regression coverage reduce user-facing risk.
- **Service boundaries**: **Pass** - frontend-only change, no new cross-service coupling.

## Project Structure

### Documentation (this feature)

```text
specs/006-chat-message-presentation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── chat-rendering-behavior.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── components/      # chat message UI and presentation
│   │   ├── services/        # assistant response normalization
│   │   └── lib/             # markdown/render helpers
│   └── ...
└── tests/
    ├── unit/                # renderer/normalizer tests
    └── e2e/                 # Playwright chat rendering journeys
```

**Structure Decision**: Keep all implementation and tests in `frontend` to preserve service boundaries and reuse existing TypeScript libraries and test infrastructure.

## Phase 0 — Research (`research.md`)

Resolve markdown rendering and safety approach, define library reuse policy, and codify Playwright best practices for deterministic E2E tests.

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- Define normalized display message and rendering policy model.
- Document UI behavior contract for markdown elements, remote images, and table overflow.
- Define quickstart commands for unit + Playwright verification.

## Re-evaluated Constitution Check (Post-design)

- **Community benefit**: **Pass**
- **Trustworthy retrieval**: **Pass**
- **Data stewardship**: **Pass**
- **Safety & quality**: **Pass**
- **Service boundaries**: **Pass**

## Complexity Tracking

No constitution violations requiring exceptions.

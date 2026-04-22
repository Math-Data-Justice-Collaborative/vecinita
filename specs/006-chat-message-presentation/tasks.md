# Tasks: Chat Message Presentation

**Input**: Design documents from `/specs/006-chat-message-presentation/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/chat-rendering-behavior.md`, `quickstart.md`

**Tests**: Include unit/integration and Playwright E2E coverage because the specification and plan explicitly require rendering behavior verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., `US1`, `US2`, `US3`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align test harness and dependency reuse strategy before implementation.

- [X] T001 Audit existing markdown/sanitization dependencies and record reuse decision in `specs/006-chat-message-presentation/implementation-notes.md`
- [X] T002 Update rendering test fixture payloads for markdown/table/html/image cases in `frontend/src/app/components/__tests__/ChatMessage.sources.test.tsx`
- [X] T003 [P] Add Playwright deterministic fixture helpers for chat rendering scenarios in `frontend/tests/e2e/chat-rendering.fixtures.ts`
- [X] T004 [P] Verify Playwright Chromium-first project setup for this feature in `frontend/playwright.config.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared rendering policy and normalization infrastructure used by all stories.

**⚠️ CRITICAL**: No user story work should begin before this phase is complete.

- [X] T005 Create render policy types for markdown/html/image/table behavior in `frontend/src/app/types/agent.ts`
- [X] T006 [P] Implement assistant payload normalization utility in `frontend/src/app/lib/assistantMessageNormalization.ts`
- [X] T007 [P] Implement markdown rendering policy transformer (HTML strip/escape, remote image link mode) in `frontend/src/app/lib/assistantMarkdownPolicy.ts`
- [X] T008 Wire normalization + render policy into chat data flow in `frontend/src/app/hooks/useAgentChat.ts`
- [X] T009 Add foundational unit coverage for normalization and policy transformation in `frontend/src/app/lib/__tests__/assistantMarkdownPolicy.test.ts`

**Checkpoint**: Foundation ready - user stories can now proceed.

---

## Phase 3: User Story 1 - Readable Agent Replies (Priority: P1) 🎯 MVP

**Goal**: Render assistant replies as clean, readable markdown text without exposing raw payload metadata.

**Independent Test**: Submit a chat prompt and verify assistant bubble shows semantic content only, including readable markdown structure, with no raw payload object syntax.

### Tests for User Story 1

- [X] T010 [P] [US1] Add integration test for semantic assistant message rendering and metadata suppression in `frontend/src/app/components/__tests__/ChatInterface.integration.test.tsx`
- [X] T011 [P] [US1] Add Playwright E2E for markdown readability and metadata exclusion in `frontend/tests/e2e/chat-markdown-rendering.spec.ts`

### Implementation for User Story 1

- [X] T012 [US1] Update assistant response extraction logic to use semantic message content in `frontend/src/app/services/agentService.ts`
- [X] T013 [US1] Implement markdown-rendered assistant message body in `frontend/src/app/components/ChatMessage.tsx`
- [X] T014 [US1] Prevent raw metadata fields from rendering in chat bubbles in `frontend/src/app/components/ChatMessage.tsx`
- [X] T015 [US1] Add/adjust component tests for paragraph, list, link, and code block rendering in `frontend/src/app/components/__tests__/ChatWidget.test.tsx`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Clear Visual Hierarchy in Conversation (Priority: P2)

**Goal**: Ensure user vs assistant messages are visually distinct and consistently readable across conversation turns.

**Independent Test**: Render mixed multi-turn conversation and verify sender distinction, consistent spacing/typography, and stable long-thread readability.

### Tests for User Story 2

- [X] T016 [P] [US2] Add integration assertions for sender-specific visual treatment in `frontend/src/app/components/__tests__/ChatWidget.stream-success.integration.test.tsx`
- [X] T017 [P] [US2] Add Playwright E2E for mixed-thread visual hierarchy and long-message layout stability in `frontend/tests/e2e/chat-visual-hierarchy.spec.ts`

### Implementation for User Story 2

- [X] T018 [US2] Refine role-based chat bubble styling and typography in `frontend/src/app/components/ChatMessage.tsx`
- [X] T019 [US2] Update conversation container spacing and overflow behavior for long assistant output in `frontend/src/app/components/ChatWidget.tsx`
- [X] T020 [US2] Preserve chat input usability during long rendered assistant messages in `frontend/src/app/pages/ChatPage.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Graceful Handling of Missing or Irregular Content (Priority: P3)

**Goal**: Handle missing content and irregular payloads safely while preserving chat continuity.

**Independent Test**: Simulate empty content, raw HTML, remote image URLs, and wide tables; verify fallback behavior and safe rendering policy.

### Tests for User Story 3

- [X] T021 [P] [US3] Add unit tests for fallback behavior, HTML stripping, and remote image link conversion in `frontend/src/app/components/__tests__/ChatMessage.sources.test.tsx`
- [X] T022 [P] [US3] Add Playwright E2E for fallback, remote image link-only mode, and wide-table horizontal scroll in `frontend/tests/e2e/chat-edge-cases.spec.ts`

### Implementation for User Story 3

- [X] T023 [US3] Implement user-friendly fallback message behavior for empty assistant content in `frontend/src/app/components/ChatMessage.tsx`
- [X] T024 [US3] Enforce remote image rendering as clickable links (no inline loading) in `frontend/src/app/lib/assistantMarkdownPolicy.ts`
- [X] T025 [US3] Enforce wide table horizontal scrolling within message bounds in `frontend/src/app/components/ChatMessage.tsx`
- [X] T026 [US3] Ensure raw HTML is escaped/stripped before render in `frontend/src/app/lib/assistantMarkdownPolicy.ts`

**Checkpoint**: All user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, docs alignment, and full validation.

- [X] T027 [P] Update contract and quickstart validation notes after implementation in `specs/006-chat-message-presentation/contracts/chat-rendering-behavior.md`
- [X] T028 [P] Align feature documentation with final test commands in `specs/006-chat-message-presentation/quickstart.md`
- [X] T029 [P] Define and document usability measurement protocol for sender identification/readability metrics (SC-002, SC-004) in `specs/006-chat-message-presentation/acceptance-measurement.md`
- [X] T030 Run full frontend test suite (unit + integration + Playwright) and record outcomes in `specs/006-chat-message-presentation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; defines MVP.
- **Phase 4 (US2)**: Depends on Phase 2; can proceed after US1 baseline if staffing allows.
- **Phase 5 (US3)**: Depends on Phase 2; can proceed after US1 baseline if staffing allows.
- **Phase 6 (Polish)**: Depends on completion of all targeted user stories.

### User Story Dependencies

- **US1 (P1)**: Independent once foundation is complete.
- **US2 (P2)**: Independent once foundation is complete; leverages shared message components from US1.
- **US3 (P3)**: Independent once foundation is complete; leverages shared policy/normalization from foundation.

### Within Each User Story

- Write tests first and confirm failing assertions before implementation.
- Implement data/policy transformation before UI wiring where applicable.
- Complete story-level implementation before broad polish.

### Parallel Opportunities

- **Setup**: `T003` and `T004` can run in parallel.
- **Foundational**: `T006` and `T007` can run in parallel after `T005`.
- **US1**: `T010` and `T011` can run in parallel; implementation tasks then proceed sequentially.
- **US2**: `T016` and `T017` can run in parallel; `T018`-`T020` then execute in order.
- **US3**: `T021` and `T022` can run in parallel; `T023`-`T026` then execute in order.
- **Polish**: `T027`, `T028`, and `T029` can run in parallel before `T030`.

---

## Parallel Example: User Story 1

```bash
# Parallel test authoring for US1:
Task: "T010 [US1] Add integration test in frontend/src/app/components/__tests__/ChatInterface.integration.test.tsx"
Task: "T011 [US1] Add Playwright E2E in frontend/tests/e2e/chat-markdown-rendering.spec.ts"

# Then implement US1 behavior:
Task: "T012 [US1] Update semantic extraction in frontend/src/app/services/agentService.ts"
Task: "T013 [US1] Implement markdown-rendered assistant message in frontend/src/app/components/ChatMessage.tsx"
```

---

## Parallel Example: User Story 2

```bash
# Parallel test authoring for US2:
Task: "T016 [US2] Add integration visual hierarchy checks in frontend/src/app/components/__tests__/ChatWidget.stream-success.integration.test.tsx"
Task: "T017 [US2] Add Playwright hierarchy/layout test in frontend/tests/e2e/chat-visual-hierarchy.spec.ts"
```

---

## Parallel Example: User Story 3

```bash
# Parallel test authoring for US3:
Task: "T021 [US3] Add fallback/html/image unit tests in frontend/src/app/components/__tests__/ChatMessage.sources.test.tsx"
Task: "T022 [US3] Add edge-case Playwright E2E in frontend/tests/e2e/chat-edge-cases.spec.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently via `T010` and `T011`.
4. Demo/deploy MVP if acceptable.

### Incremental Delivery

1. Foundation complete (Phases 1-2).
2. Deliver US1 (MVP), validate, and stabilize.
3. Deliver US2, validate sender hierarchy/layout.
4. Deliver US3, validate edge-case safety behavior.
5. Run Phase 6 full validation.

### Parallel Team Strategy

1. Team collaborates on Phase 1 and Phase 2.
2. After foundation:
   - Developer A: US1
   - Developer B: US2
   - Developer C: US3
3. Converge on polish and final regression run.

---

## Notes

- Tasks marked `[P]` are parallel-safe by file separation and dependency order.
- Story labels map directly to `spec.md` user stories for traceability.
- Every task includes an explicit file path to keep execution unambiguous.

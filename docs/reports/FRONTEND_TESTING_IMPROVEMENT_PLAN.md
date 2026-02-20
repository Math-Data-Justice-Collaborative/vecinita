# Frontend Testing Improvement Plan

## Goals
- Catch chat stream regressions (thinking/tool/clarification/complete/error).
- Increase confidence in page-level chat UX behavior.
- Make test execution consistent in local and CI.

## Priority 1: Streaming Contract Coverage
1. Add unit tests for `useAgentChat` covering:
   - `tool_event` start/result/error handling.
   - clarification persistence in message history.
   - complete event with/without sources.
2. Add unit tests for `agentService.askStream`:
   - SSE parse success path.
   - malformed JSON resilience.
   - timeout and connection error handling.

## Priority 2: Page/Component Integration Coverage
1. Add `ChatPage` integration tests with mocked `useAgentChat`:
   - renders message history.
   - shows transient progress panel while loading.
   - retry button behavior on error.
2. Add `ChatWidget` integration tests for the same critical states.

## Priority 3: Test Quality and CI Hardening
1. Replace placeholder tests (smoke/import-only) with behavior assertions.
2. Enforce minimum coverage gates for:
   - `src/app/hooks/useAgentChat.ts`
   - `src/app/services/agentService.ts`
   - `src/app/pages/ChatPage.tsx`
3. Add dedicated npm scripts:
   - `test:unit` (fast, no watch)
   - `test:ci` (coverage + reporters)

## Proposed Milestones
- Milestone A: Hook + service tests complete.
- Milestone B: ChatPage + ChatWidget integration tests complete.
- Milestone C: CI coverage threshold + flaky test cleanup.

## Execution Commands
- `cd frontend && npm run test`
- `cd frontend && npm run test:coverage`

## Exit Criteria
- Streaming chat regressions are caught by automated tests before merge.
- No placeholder chat tests remain in the primary chat flow.
- Coverage for the chat flow files is consistently reported in CI.

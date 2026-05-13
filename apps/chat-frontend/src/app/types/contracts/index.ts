/**
 * Interim **FR-010** wire contracts for the chat SPA (`agentService` + future Pact).
 * Thin re-exports of `types/agent` until a future feature adds chat-side OpenAPI codegen.
 *
 * @see specs/005-wire-services-dm-front/data-model.md §Typed testing artifacts
 */
export type {
  AgentConfig,
  AgentResponse,
  AgentSource,
  AskQueryParams,
  StreamEvent,
  StreamEventComplete,
} from '../agent';

export { isClarificationEvent, isCompleteEvent, isErrorEvent, isThinkingEvent } from '../agent';

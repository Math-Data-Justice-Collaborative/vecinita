/**
 * TypeScript interfaces for Backend Agent Integration
 *
 * Defines types for agent API responses, streaming events, and configurations.
 */

export interface AgentSource {
  title: string;
  url: string;
  type?: 'document' | 'link' | 'web';
  isDownload?: boolean;
  chunkIndex?: number;
  metadata?: Record<string, unknown>;
  snippet?: string;
}

export interface AgentResponse {
  answer: string;
  sources: AgentSource[];
  thread_id?: string;
  suggested_questions?: string[];
  language?: string;
  model?: string;
}

export interface RenderPolicy {
  allowMarkdown: boolean;
  allowRawHtml: false;
  remoteImageMode: 'link_only';
  tableOverflowMode: 'horizontal_scroll';
}

export interface StreamEventThinking {
  type: 'thinking';
  message: string;
  toolName?: string;
  stage?: string;
  progress?: number;
  status?: 'working' | 'waiting' | 'error';
  waiting?: boolean;
  tool?: string;
  timestamp?: string;
}

export interface StreamEventToken {
  type: 'token';
  content: string;
  cumulative?: string;
}

export interface StreamEventSource {
  type: 'source';
  url: string;
  title: string;
  source_type?: 'document' | 'link';
}

export interface StreamEventComplete {
  type: 'complete';
  answer: string;
  sources: AgentSource[];
  suggested_questions?: string[];
  suggestedQuestions?: string[];
  thread_id?: string;
  plan?: string;
  metadata?: {
    model_used?: string;
    tokens?: number;
    progress?: number;
    stage?: string;
  };
  timestamp?: string;
}

export interface StreamEventClarification {
  type: 'clarification';
  message?: string;
  questions?: string[];
  context?: string;
  suggestedQuestions?: string[];
  stage?: string;
  progress?: number;
  waiting?: boolean;
  timestamp?: string;
}

export interface StreamEventError {
  type: 'error';
  message: string;
  code?: string;
  stage?: string;
  progress?: number;
  status?: 'error';
  timestamp?: string;
}

export interface StreamEventToolEvent {
  type: 'tool_event';
  phase: 'start' | 'result' | 'error';
  tool?: string;
  message: string;
  stage?: string;
  progress?: number;
  status?: 'working' | 'waiting' | 'error';
  waiting?: boolean;
  transient?: boolean;
  timestamp?: string;
}

export type StreamEvent =
  | StreamEventThinking
  | StreamEventToken
  | StreamEventSource
  | StreamEventComplete
  | StreamEventClarification
  | StreamEventError
  | StreamEventToolEvent;

export interface AgentConfig {
  providers: Array<{
    name: string;
    models: string[];
    default: boolean;
  }>;
  models: Record<string, string[]>;
  defaultProvider?: string;
  defaultModel?: string;
}

export interface AskQueryParams {
  question: string;
  thread_id?: string;
  context_answer?: string;
  lang?: 'en' | 'es';
  provider?: string;
  model?: string;
  clarification_response?: string;
}

// Type guards for stream events
export function isThinkingEvent(event: StreamEvent): event is StreamEventThinking {
  return event.type === 'thinking';
}

export function isCompleteEvent(event: StreamEvent): event is StreamEventComplete {
  return event.type === 'complete';
}

export function isClarificationEvent(event: StreamEvent): event is StreamEventClarification {
  return event.type === 'clarification';
}

export function isErrorEvent(event: StreamEvent): event is StreamEventError {
  return event.type === 'error';
}

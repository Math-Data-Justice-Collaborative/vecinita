/**
 * Agent Service — API Client for the Vecinita LangGraph Agent
 *
 * Handles all communication with the backend agent service, supporting both
 * streaming (Server-Sent Events) and non-streaming request modes.
 *
 * ## Architecture
 * Requests are routed through the Unified API Gateway
 * (``VITE_GATEWAY_URL``) in normal deployments.  When the frontend is hosted
 * on ``*.onrender.com`` and the GATEWAY_URL resolves to the agent's Render
 * service directly, the client transparently adjusts path prefixes and the
 * config endpoint URL so that all calls reach the correct handler.
 *
 * ## Environment variables
 * - ``VITE_GATEWAY_URL``  — preferred gateway base URL
 * - ``VITE_BACKEND_URL`` — fallback gateway URL
 * - ``VITE_AGENT_REQUEST_TIMEOUT_MS`` — timeout for non-stream requests
 * - ``VITE_AGENT_STREAM_TIMEOUT_MS`` — overall timeout for stream requests
 * - ``VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS`` — first SSE event timeout
 * - ``VITE_AGENT_DEBUG`` — set to ``'true'`` to emit debug CustomEvents
 */

import type {
  AgentResponse,
  AgentConfig,
  AskQueryParams,
  StreamEvent,
  StreamEventComplete,
} from '../types/contracts';
import {
  isDirectRenderAgentHost,
  normalizeAgentApiBaseUrl,
  resolveGatewayUrl,
} from '../lib/agentApiResolution';
import { extractAssistantTextFromPayload } from '../lib/assistantMessageNormalization';
import { parseJsonResponseOrThrow } from '../lib/responseParser';

// Get gateway URL from environment or fallback to localhost
// In development with Vite proxy, use /api prefix
const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  (import.meta.env.DEV ? '/api' : 'http://localhost:8004/api/v1');

export interface AgentServiceTimeouts {
  requestMs: number;
  streamMs: number;
  firstEventMs: number;
}

function parsePositiveTimeoutMs(rawValue: string | undefined, fallbackMs: number): number {
  const parsedValue = Number(rawValue);
  if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
    return fallbackMs;
  }

  return Math.floor(parsedValue);
}

export function resolveAgentServiceTimeouts(
  env: Partial<ImportMetaEnv> = (import.meta as ImportMeta).env ?? {}
): AgentServiceTimeouts {
  return {
    requestMs: parsePositiveTimeoutMs(env.VITE_AGENT_REQUEST_TIMEOUT_MS, 90000),
    streamMs: parsePositiveTimeoutMs(env.VITE_AGENT_STREAM_TIMEOUT_MS, 120000),
    firstEventMs: parsePositiveTimeoutMs(env.VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS, 15000),
  };
}

const DEFAULT_AGENT_SERVICE_TIMEOUTS = resolveAgentServiceTimeouts();

const isAgentDebugEnabled = (): boolean => {
  if ((import.meta as ImportMeta).env?.VITE_AGENT_DEBUG === 'true') {
    return true;
  }

  if (typeof window !== 'undefined' && window.localStorage.getItem('vecinita_debug_chat') === '1') {
    return true;
  }

  return false;
};

function emitAgentDebugEvent(scope: string, message: string, data?: unknown): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(
    new CustomEvent('vecinita:agent-debug', {
      detail: { scope, message, data },
    })
  );
}

export class AgentServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'AgentServiceError';
  }
}

/**
 * Normalise a raw agent config payload into the canonical {@link AgentConfig}
 * shape expected by the frontend.
 *
 * The direct agent ``GET /config`` response uses ``{ key, label }`` fields
 * for providers rather than the ``{ name, models }`` shape expected by the
 * frontend.  This function accepts either shape and maps both to the
 * canonical form so that the rest of the UI can work with one consistent
 * interface regardless of which endpoint was called.
 *
 * @param rawConfig - Untyped JSON payload from the agent or gateway config
 *                    endpoint.
 * @returns Validated and normalised {@link AgentConfig}.
 * @throws {@link AgentServiceError} when the payload is fundamentally
 *         malformed (not an object, no providers at all).
 */
function normalizeAgentConfig(rawConfig: unknown): AgentConfig {
  if (!rawConfig || typeof rawConfig !== 'object') {
    throw new AgentServiceError('Agent config payload is malformed', 0, 'INVALID_CONFIG_PAYLOAD');
  }

  const source = rawConfig as Record<string, unknown>;
  const modelsRecord =
    source.models && typeof source.models === 'object' && !Array.isArray(source.models)
      ? (source.models as Record<string, unknown>)
      : {};

  const normalizedModels: Record<string, string[]> = {};
  for (const [providerName, providerModels] of Object.entries(modelsRecord)) {
    if (Array.isArray(providerModels)) {
      normalizedModels[providerName] = providerModels.filter(
        (entry): entry is string => typeof entry === 'string'
      );
    }
  }

  const providersSource = Array.isArray(source.providers) ? source.providers : [];
  const normalizedProviders: AgentConfig['providers'] = providersSource
    .map((provider, index) => {
      if (!provider || typeof provider !== 'object') {
        return null;
      }

      const providerRecord = provider as Record<string, unknown>;
      const providerName =
        typeof providerRecord.name === 'string'
          ? providerRecord.name
          : typeof providerRecord.key === 'string'
            ? providerRecord.key
            : '';

      if (!providerName) {
        return null;
      }

      const inlineModels = Array.isArray(providerRecord.models)
        ? providerRecord.models.filter((entry): entry is string => typeof entry === 'string')
        : undefined;
      const mappedModels = normalizedModels[providerName] ?? [];

      return {
        name: providerName,
        models: inlineModels ?? mappedModels,
        default: typeof providerRecord.default === 'boolean' ? providerRecord.default : index === 0,
      };
    })
    .filter((provider): provider is AgentConfig['providers'][number] => provider !== null);

  if (normalizedProviders.length === 0) {
    for (const [providerName, providerModels] of Object.entries(normalizedModels)) {
      normalizedProviders.push({
        name: providerName,
        models: providerModels,
        default: normalizedProviders.length === 0,
      });
    }
  }

  if (normalizedProviders.length === 0) {
    throw new AgentServiceError(
      'Agent config payload has no providers',
      0,
      'INVALID_CONFIG_PAYLOAD'
    );
  }

  return {
    providers: normalizedProviders,
    models: normalizedModels,
    defaultProvider:
      typeof source.defaultProvider === 'string'
        ? source.defaultProvider
        : normalizedProviders[0]?.name,
    defaultModel:
      typeof source.defaultModel === 'string'
        ? source.defaultModel
        : normalizedProviders[0]?.models[0],
  };
}

class AgentServiceClient {
  private baseUrl: string;
  private timeouts: AgentServiceTimeouts;

  constructor(baseUrl: string = GATEWAY_URL, timeouts: Partial<AgentServiceTimeouts> = {}) {
    this.baseUrl = normalizeAgentApiBaseUrl(
      resolveGatewayUrl(baseUrl, (import.meta.env.VITE_BACKEND_URL || '').trim())
    );
    this.timeouts = {
      requestMs: timeouts.requestMs ?? DEFAULT_AGENT_SERVICE_TIMEOUTS.requestMs,
      streamMs: timeouts.streamMs ?? DEFAULT_AGENT_SERVICE_TIMEOUTS.streamMs,
      firstEventMs: timeouts.firstEventMs ?? DEFAULT_AGENT_SERVICE_TIMEOUTS.firstEventMs,
    };
  }

  private debugLog(message: string, data?: unknown): void {
    if (!isAgentDebugEnabled()) {
      return;
    }

    emitAgentDebugEvent('agentService', message, data);
  }

  private buildEndpointUrl(path: string): URL {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    const normalizedBase = this.baseUrl.endsWith('/') ? this.baseUrl.slice(0, -1) : this.baseUrl;

    if (/^https?:\/\//i.test(normalizedBase)) {
      return new URL(`${normalizedBase}${normalizedPath}`);
    }

    const fallbackOrigin =
      typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
    return new URL(`${normalizedBase}${normalizedPath}`, fallbackOrigin);
  }

  /**
   * Build the URL for the agent configuration endpoint.
   *
   * The correct config endpoint differs depending on how the frontend
   * reaches the backend:
   *
   * - **Direct Render agent host** (``vecinita-agent.onrender.com``) —
   *   the agent exposes config at ``GET /config`` (no gateway prefix).
   * - **Unified gateway** — config is at ``GET /ask/config`` because the
   *   gateway namespaces agent routes under ``/ask``.
   *
   * @returns Fully-qualified {@link URL} for the config endpoint.
   */
  private buildConfigUrl(): URL {
    const normalizedBase = this.baseUrl.endsWith('/') ? this.baseUrl.slice(0, -1) : this.baseUrl;

    if (/^https?:\/\//i.test(normalizedBase)) {
      try {
        const parsed = new URL(normalizedBase);
        if (isDirectRenderAgentHost(parsed.hostname)) {
          return this.buildEndpointUrl('/config');
        }
      } catch {
        // Fall through to the default gateway-style config path.
      }
    }

    return this.buildEndpointUrl('/ask/config');
  }

  private buildConfigFallbackUrls(): string[] {
    const primaryUrl = this.buildConfigUrl().toString();
    const candidates: string[] = [primaryUrl];
    const seen = new Set(candidates);

    const addCandidate = (candidate: string) => {
      if (!candidate || seen.has(candidate)) {
        return;
      }
      seen.add(candidate);
      candidates.push(candidate);
    };

    const currentOrigin = typeof window !== 'undefined' ? window.location.origin : '';
    const currentHostname = typeof window !== 'undefined' ? window.location.hostname : '';
    const isCurrentHostLocal =
      currentHostname === 'localhost' ||
      currentHostname === '127.0.0.1' ||
      currentHostname === '::1';

    try {
      const primary = new URL(primaryUrl);
      if (primary.pathname.endsWith('/ask/config')) {
        addCandidate(this.buildEndpointUrl('/config').toString());
      } else if (primary.pathname.endsWith('/config')) {
        addCandidate(this.buildEndpointUrl('/ask/config').toString());
      }

      const isLocalTarget =
        primary.hostname === 'localhost' ||
        primary.hostname === '127.0.0.1' ||
        primary.hostname === '::1';
      if (currentOrigin && isLocalTarget && !isCurrentHostLocal) {
        addCandidate(new URL('/api/v1/ask/config', currentOrigin).toString());
      }
    } catch {
      // Best-effort fallback set only.
    }

    if (currentOrigin) {
      addCandidate(new URL('/api/v1/ask/config', currentOrigin).toString());
    }

    return candidates;
  }

  /**
   * Ask a question and get a complete response (non-streaming).
   */
  private normalizeAskResponse(rawResponse: unknown): AgentResponse {
    if (!rawResponse || typeof rawResponse !== 'object') {
      throw new AgentServiceError('Agent response payload is malformed', 0, 'INVALID_ASK_PAYLOAD');
    }

    const response = rawResponse as Record<string, unknown>;
    const answer = extractAssistantTextFromPayload(rawResponse);
    const sources = Array.isArray(response.sources)
      ? response.sources.filter((source): source is AgentResponse['sources'][number] => {
          return (
            Boolean(source) &&
            typeof source === 'object' &&
            typeof (source as Record<string, unknown>).title === 'string' &&
            typeof (source as Record<string, unknown>).url === 'string'
          );
        })
      : [];

    return {
      answer,
      sources,
      thread_id: typeof response.thread_id === 'string' ? response.thread_id : undefined,
      suggested_questions: Array.isArray(response.suggested_questions)
        ? response.suggested_questions.filter((item): item is string => typeof item === 'string')
        : undefined,
      language: typeof response.language === 'string' ? response.language : undefined,
      model: typeof response.model === 'string' ? response.model : undefined,
    };
  }

  async ask(params: AskQueryParams): Promise<AgentResponse> {
    const url = this.buildEndpointUrl('/ask');

    // Add query parameters
    url.searchParams.append('question', params.question);
    if (params.thread_id) {
      url.searchParams.append('thread_id', params.thread_id);
    }
    if (params.context_answer) {
      url.searchParams.append('context_answer', params.context_answer);
    }
    if (params.lang) {
      url.searchParams.append('lang', params.lang);
    }
    if (params.provider) {
      url.searchParams.append('provider', params.provider);
    }
    if (params.model) {
      url.searchParams.append('model', params.model);
    }
    if (params.clarification_response) {
      url.searchParams.append('clarification_response', params.clarification_response);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeouts.requestMs);

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new AgentServiceError(`Agent request failed: ${errorText}`, response.status);
      }

      const parsedResponse = await parseJsonResponseOrThrow<unknown, AgentServiceError>(
        response,
        '/ask',
        {
          errorFactory: (message, statusCode, code) =>
            new AgentServiceError(message, statusCode, code),
          nonJsonHint: 'This usually indicates a gateway URL/proxy misconfiguration.',
          invalidJsonHint: 'This usually indicates a gateway URL/proxy misconfiguration.',
        }
      );

      return this.normalizeAskResponse(parsedResponse);
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof AgentServiceError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new AgentServiceError('Request timeout - please try again', 504, 'TIMEOUT');
        }
        throw new AgentServiceError(`Network error: ${error.message}`, 0, 'NETWORK_ERROR');
      }

      throw new AgentServiceError('Unknown error occurred', 0, 'UNKNOWN');
    }
  }

  /**
   * Ask a question and stream the response via Server-Sent Events.
   *
   * @param params Query parameters
   * @param onEvent Callback for each streaming event
   * @returns Promise that resolves when stream completes
   */
  async askStream(params: AskQueryParams, onEvent: (event: StreamEvent) => void): Promise<void> {
    const url = this.buildEndpointUrl('/ask/stream');

    // Add query parameters
    url.searchParams.append('question', params.question);
    if (params.thread_id) {
      url.searchParams.append('thread_id', params.thread_id);
    }
    if (params.context_answer) {
      url.searchParams.append('context_answer', params.context_answer);
    }
    if (params.lang) {
      url.searchParams.append('lang', params.lang);
    }
    if (params.provider) {
      url.searchParams.append('provider', params.provider);
    }
    if (params.model) {
      url.searchParams.append('model', params.model);
    }
    if (params.clarification_response) {
      url.searchParams.append('clarification_response', params.clarification_response);
    }

    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(url.toString());
      const timeoutId = setTimeout(() => {
        eventSource.close();
        reject(
          new AgentServiceError('Stream timeout - request took too long', 504, 'STREAM_TIMEOUT')
        );
      }, this.timeouts.streamMs);

      let firstEventReceived = false;
      let firstEventTimeoutId: ReturnType<typeof setTimeout> | null = null;
      let eventCount = 0;
      const clearFirstEventTimeout = () => {
        if (firstEventTimeoutId) {
          clearTimeout(firstEventTimeoutId);
          firstEventTimeoutId = null;
        }
      };

      firstEventTimeoutId = setTimeout(() => {
        if (firstEventReceived) {
          return;
        }
        this.debugLog('askStream:first_event_timeout', {
          thread_id: params.thread_id,
          questionLength: (params.question || '').length,
        });
        clearTimeout(timeoutId);
        eventSource.close();
        reject(new AgentServiceError('Stream stalled before first event', 408, 'STREAM_STALLED'));
      }, this.timeouts.firstEventMs);

      eventSource.onmessage = (event) => {
        let data: StreamEvent;
        try {
          data = JSON.parse(event.data) as StreamEvent;
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
          return;
        }

        eventCount += 1;
        if (!firstEventReceived) {
          firstEventReceived = true;
          clearFirstEventTimeout();
          this.debugLog('askStream:first_event_received', {
            thread_id: params.thread_id,
            eventCount,
          });
        }

        if (data.type === 'complete') {
          const complete = data as StreamEventComplete;
          const rawSuggestions = complete.suggested_questions ?? complete.suggestedQuestions;

          if (Array.isArray(rawSuggestions)) {
            complete.suggestedQuestions = rawSuggestions.filter(
              (item): item is string => typeof item === 'string' && item.trim().length > 0
            );
          }

          data = complete;
        }

        try {
          onEvent(data);
        } catch (callbackError) {
          clearTimeout(timeoutId);
          clearFirstEventTimeout();
          eventSource.close();

          if (callbackError instanceof AgentServiceError) {
            reject(callbackError);
            return;
          }

          reject(
            new AgentServiceError(
              callbackError instanceof Error ? callbackError.message : 'Stream callback failed',
              0,
              'STREAM_CALLBACK_ERROR'
            )
          );
          return;
        }

        // Close stream on completion or error
        if (data.type === 'complete') {
          clearTimeout(timeoutId);
          clearFirstEventTimeout();
          eventSource.close();
          this.debugLog('askStream:complete', {
            thread_id: params.thread_id,
            eventCount,
          });
          resolve();
          return;
        }

        if (data.type === 'error') {
          clearTimeout(timeoutId);
          clearFirstEventTimeout();
          eventSource.close();
          reject(new AgentServiceError(data.message, undefined, data.code));
        }
      };

      eventSource.onerror = (error) => {
        clearTimeout(timeoutId);
        clearFirstEventTimeout();
        eventSource.close();
        this.debugLog('askStream:error', {
          thread_id: params.thread_id,
          eventCount,
          firstEventReceived,
          error,
        });
        reject(new AgentServiceError('Stream connection failed', 0, 'STREAM_ERROR'));
      };
    });
  }

  /**
   * Get agent configuration (available providers and models).
   */
  async getConfig(): Promise<AgentConfig> {
    const configUrls = this.buildConfigFallbackUrls();
    const CONFIG_RETRY_ATTEMPTS = 3;
    const CONFIG_RETRY_DELAY_MS = 800;
    let lastError: unknown;

    for (const url of configUrls) {
      for (let attempt = 1; attempt <= CONFIG_RETRY_ATTEMPTS; attempt += 1) {
        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              Accept: 'application/json',
            },
          });

          if (!response.ok) {
            throw new AgentServiceError('Failed to fetch agent configuration', response.status);
          }

          const rawConfig = await parseJsonResponseOrThrow<unknown, AgentServiceError>(
            response,
            '/ask/config',
            {
              errorFactory: (message, statusCode, code) =>
                new AgentServiceError(message, statusCode, code),
              nonJsonHint: 'This usually indicates a gateway URL/proxy misconfiguration.',
              invalidJsonHint: 'This usually indicates a gateway URL/proxy misconfiguration.',
            }
          );
          return normalizeAgentConfig(rawConfig);
        } catch (error) {
          lastError = error;
          if (
            error instanceof AgentServiceError &&
            (error.code === 'INVALID_RESPONSE_FORMAT' || error.code === 'INVALID_JSON')
          ) {
            throw error;
          }
          const isLastAttempt = attempt === CONFIG_RETRY_ATTEMPTS;
          const isRetriableNetworkError = !(error instanceof AgentServiceError);

          if (isLastAttempt || !isRetriableNetworkError) {
            break;
          }

          await new Promise((resolve) => setTimeout(resolve, CONFIG_RETRY_DELAY_MS));
        }
      }
    }

    if (lastError instanceof AgentServiceError) {
      throw lastError;
    }

    throw new AgentServiceError('Failed to connect to agent service', 0, 'NETWORK_ERROR');
  }

  /**
   * Check if agent service is available.
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(this.buildEndpointUrl('/health').toString(), {
        method: 'GET',
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const agentService = new AgentServiceClient();

// Export class for testing
export { AgentServiceClient };

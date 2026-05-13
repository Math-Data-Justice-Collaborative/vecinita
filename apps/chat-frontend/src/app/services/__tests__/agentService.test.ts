/**
 * Tests for agentService.ts
 *
 * Tests agent API client functionality including requests, streaming, and error handling.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  agentService,
  AgentServiceClient,
  AgentServiceError,
  resolveAgentServiceTimeouts,
} from '../agentService';
import type { AskQueryParams, AgentResponse, AgentConfig, StreamEvent } from '../../types/agent';

// Mock fetch
globalThis.fetch = vi.fn();

// Mock EventSource
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
  }

  close() {}
}

globalThis.EventSource = MockEventSource as unknown as typeof EventSource;

const fetchMock = vi.mocked(globalThis.fetch);

function createMessageEvent(data: string): MessageEvent<string> {
  return new MessageEvent('message', { data });
}

function installMockEventSource() {
  class TestEventSource {
    static latestInstance: TestEventSource | null = null;

    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    url: string;
    closed = false;

    constructor(url: string) {
      this.url = url;
      TestEventSource.latestInstance = this;
    }

    close() {
      this.closed = true;
    }
  }

  globalThis.EventSource = TestEventSource as unknown as typeof EventSource;
  return TestEventSource;
}

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  if (!headers.has('content-type')) {
    headers.set('content-type', 'application/json; charset=utf-8');
  }

  return new Response(JSON.stringify(body), {
    ...init,
    headers,
  });
}

describe('AgentServiceClient', () => {
  let client: AgentServiceClient;

  beforeEach(() => {
    vi.clearAllMocks();
    client = new AgentServiceClient('http://localhost:8002');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('ask', () => {
    it('should make successful request', async () => {
      const mockResponse: AgentResponse = {
        answer: 'Test answer',
        sources: [],
        thread_id: 'thread-123',
      };

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(mockResponse));

      const params: AskQueryParams = {
        question: 'What is testing?',
      };

      const result = await client.ask(params);

      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ask'),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should normalize structured payloads that return assistant message.content', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse({
          model: 'llama3.2',
          message: {
            role: 'assistant',
            content: 'Normalized from nested message content',
          },
          sources: [],
        })
      );

      const result = await client.ask({ question: 'Nested payload response?' });
      expect(result.answer).toBe('Normalized from nested message content');
      expect(result.sources).toEqual([]);
    });

    it('should include all query parameters', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'test', sources: [] }));

      const params: AskQueryParams = {
        question: 'Test question',
        thread_id: 'thread-123',
        lang: 'es',
        provider: 'groq',
        model: 'llama-3.1',
      };

      await client.ask(params);

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      // URLSearchParams encodes spaces as + or %20, both are valid
      expect(callUrl).toContain('question=Test');
      expect(callUrl).toContain('thread_id=thread-123');
      expect(callUrl).toContain('lang=es');
      expect(callUrl).toContain('provider=groq');
      expect(callUrl).toContain('model=llama-3.1');
      expect(callUrl).not.toContain('/ask/question');
    });

    it('should support relative proxy base URLs', async () => {
      const relativeClient = new AgentServiceClient('/api');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await relativeClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('/api/ask');
      expect(callUrl).toContain('question=hello');
    });

    it('should normalize absolute base URL without API prefix', async () => {
      const absoluteClient = new AgentServiceClient('http://localhost:8004');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await absoluteClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('http://localhost:8004/api/v1/ask');
      expect(callUrl).toContain('question=hello');
    });

    it('should rewrite localhost API base to public host in browser context', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: '34.55.88.67',
        origin: 'http://34.55.88.67:15173',
      } as Location);

      const publicClient = new AgentServiceClient('http://localhost:18004/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await publicClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('http://34.55.88.67:18004/api/v1/ask');
      expect(callUrl).toContain('question=hello');

      locationSpy.mockRestore();
    });

    it('should keep localhost API base when browser host is localhost', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'localhost',
        origin: 'http://localhost:15173',
      } as Location);

      const localClient = new AgentServiceClient('http://localhost:18004/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await localClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('http://localhost:18004/api/v1/ask');
      expect(callUrl).toContain('question=hello');

      locationSpy.mockRestore();
    });

    it('should rewrite stale public gateway host to current browser host', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: '34.170.200.11',
        origin: 'http://34.170.200.11:15173',
      } as Location);

      const staleHostClient = new AgentServiceClient('http://34.55.88.67:18004/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await staleHostClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('http://34.170.200.11:18004/api/v1/ask');
      expect(callUrl).toContain('question=hello');

      locationSpy.mockRestore();
    });

    it('should infer Render agent host when configured with relative /api path', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await renderClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('https://vecinita-agent.onrender.com/ask');
      expect(callUrl).toContain('question=hello');

      locationSpy.mockRestore();
    });

    it('should strip gateway prefix for absolute Render agent hosts', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('https://vecinita-agent.onrender.com/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await renderClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('https://vecinita-agent.onrender.com/ask');
      expect(callUrl).not.toContain('/api/v1/ask');

      locationSpy.mockRestore();
    });

    it('should bypass an absolute Render gateway host and use the direct agent host', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('https://vecinita-gateway.onrender.com/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await renderClient.ask({ question: 'hello' });

      const callUrl = String(fetchMock.mock.calls[0]?.[0]);
      expect(callUrl).toContain('https://vecinita-agent.onrender.com/ask');
      expect(callUrl).not.toContain('vecinita-gateway.onrender.com');

      locationSpy.mockRestore();
    });

    it('should handle HTTP error', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response('Server error', {
          status: 500,
          headers: { 'content-type': 'text/plain; charset=utf-8' },
        })
      );

      await expect(client.ask({ question: 'test' })).rejects.toThrow(AgentServiceError);
    });

    it('should handle timeout', async () => {
      // Create proper AbortError with correct name
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';

      vi.mocked(fetch).mockRejectedValueOnce(abortError);

      try {
        await client.ask({ question: 'test' });
        throw new Error('Should have thrown AgentServiceError');
      } catch (error) {
        if (error instanceof AgentServiceError) {
          expect(error.code).toBe('TIMEOUT');
          expect(error.statusCode).toBe(504);
        } else {
          throw error;
        }
      }
    });

    it('should use configured request timeout override', async () => {
      const timeoutSpy = vi.spyOn(globalThis, 'setTimeout');
      const customTimeoutClient = new AgentServiceClient('http://localhost:8002', {
        requestMs: 45000,
      });

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

      await customTimeoutClient.ask({ question: 'test' });

      expect(timeoutSpy).toHaveBeenCalledWith(expect.any(Function), 45000);
    });

    it('should handle network error', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Network error'));

      await expect(client.ask({ question: 'test' })).rejects.toThrow(AgentServiceError);
    });

    it('should surface clear error when /ask returns HTML instead of JSON', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response('<!doctype html><html><body>fallback</body></html>', {
          status: 200,
          headers: { 'content-type': 'text/html; charset=utf-8' },
        })
      );

      await expect(client.ask({ question: 'test' })).rejects.toMatchObject({
        code: 'INVALID_RESPONSE_FORMAT',
      });
    });
  });

  describe('askStream', () => {
    it('should handle streaming events', async () => {
      const MockES = installMockEventSource();

      const events: StreamEvent[] = [];

      const streamPromise = client.askStream({ question: 'test' }, (event) => events.push(event));

      // Simulate EventSource events
      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"thinking","message":"Searching..."}')
          );
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"complete","answer":"Done","sources":[]}')
          );
        }
      }, 10);

      await streamPromise;

      expect(events.length).toBeGreaterThan(0);
    });

    it('should build stream URL from relative proxy base URL', async () => {
      const MockES = installMockEventSource();

      const relativeClient = new AgentServiceClient('/api');

      const streamPromise = relativeClient.askStream({ question: 'test' }, () => {});

      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"complete","answer":"Done","sources":[]}')
          );
        }
      }, 10);

      await streamPromise;
      expect(MockES.latestInstance?.url).toContain('/api/ask/stream');
      expect(MockES.latestInstance?.url).not.toContain('/ask/question');
    });

    it('should normalize stream URL when absolute base has no API prefix', async () => {
      const MockES = installMockEventSource();

      const absoluteClient = new AgentServiceClient('http://localhost:8004');
      const streamPromise = absoluteClient.askStream({ question: 'test' }, () => {});

      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"complete","answer":"Done","sources":[]}')
          );
        }
      }, 10);

      await streamPromise;
      expect(MockES.latestInstance?.url).toContain('http://localhost:8004/api/v1/ask/stream');
    });

    it('should handle malformed SSE data', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const MockES = installMockEventSource();

      const events: StreamEvent[] = [];

      const streamPromise = client.askStream({ question: 'test' }, (event) => events.push(event));

      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          // Invalid JSON should be caught and skipped
          MockES.latestInstance.onmessage(createMessageEvent('invalid json'));
          // Valid event after invalid one
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"complete","answer":"Done","sources":[]}')
          );
        }
      }, 10);

      await streamPromise;

      // Should only have 1 valid event
      expect(events.length).toBeGreaterThan(0);
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    it('should handle stream error', async () => {
      const MockES = installMockEventSource();

      const streamPromise = client.askStream({ question: 'test' }, () => {});

      setTimeout(() => {
        if (MockES.latestInstance?.onerror) {
          MockES.latestInstance.onerror(new Event('error'));
        }
      }, 10);

      await expect(streamPromise).rejects.toThrow();
    });

    it('should reject when stream callback throws AgentServiceError', async () => {
      const MockES = installMockEventSource();

      const streamPromise = client.askStream({ question: 'test' }, () => {
        throw new AgentServiceError('Connection failed: incomplete chunked read');
      });

      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          MockES.latestInstance.onmessage(
            createMessageEvent(
              '{"type":"error","message":"Connection failed: incomplete chunked read"}'
            )
          );
        }
      }, 10);

      await expect(streamPromise).rejects.toThrow(AgentServiceError);
    });

    it('should close stream on complete event', async () => {
      const MockES = installMockEventSource();

      const streamPromise = client.askStream({ question: 'test' }, () => {});

      setTimeout(() => {
        if (MockES.latestInstance?.onmessage) {
          MockES.latestInstance.onmessage(
            createMessageEvent('{"type":"complete","answer":"Done","sources":[]}')
          );
        }
      }, 10);

      await streamPromise;

      expect(MockES.latestInstance?.closed).toBe(true);
    });

    it('should reject when stream stalls before first event', async () => {
      vi.useFakeTimers();
      const MockES = installMockEventSource();

      try {
        const streamPromise = client.askStream({ question: 'test' }, () => {});
        const capturedErrorPromise = streamPromise.catch((error) => error);

        await vi.advanceTimersByTimeAsync(16000);

        const error = await capturedErrorPromise;
        expect(error).toMatchObject({ code: 'STREAM_STALLED' });
        expect(MockES.latestInstance).toBeTruthy();
      } finally {
        vi.useRealTimers();
      }
    });
  });

  describe('getConfig', () => {
    it('should fetch configuration', async () => {
      const mockConfig: AgentConfig = {
        providers: [{ name: 'groq', models: ['llama-3.1'], default: true }],
        models: { groq: ['llama-3.1'] },
      };

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(mockConfig));

      const result = await client.getConfig();

      expect(result).toMatchObject(mockConfig);
    });

    it('should handle config fetch error', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

      await expect(client.getConfig()).rejects.toThrow(AgentServiceError);
    });

    it('should use /config for direct Render agent hosts', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('https://vecinita-agent.onrender.com/api/v1');
      const mockConfig: AgentConfig = {
        providers: [{ name: 'ollama', models: ['gemma3'], default: true }],
        models: { ollama: ['gemma3'] },
      };

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(mockConfig));

      const result = await renderClient.getConfig();

      expect(result).toMatchObject(mockConfig);
      expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
        'https://vecinita-agent.onrender.com/config'
      );

      locationSpy.mockRestore();
    });

    it('should use direct agent /config when configured with an absolute Render gateway URL', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('https://vecinita-gateway.onrender.com/api/v1');
      const mockConfig: AgentConfig = {
        providers: [{ name: 'ollama', models: ['gemma3'], default: true }],
        models: { ollama: ['gemma3'] },
      };

      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(mockConfig));

      const result = await renderClient.getConfig();

      expect(result).toMatchObject(mockConfig);
      expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
        'https://vecinita-agent.onrender.com/config'
      );

      locationSpy.mockRestore();
    });

    it('should retry getConfig on transient network error', async () => {
      const mockConfig: AgentConfig = {
        providers: [{ name: 'deepseek', models: ['deepseek-chat'], default: true }],
        models: { deepseek: ['deepseek-chat'] },
      };

      vi.mocked(fetch)
        .mockRejectedValueOnce(new Error('Connection reset'))
        .mockResolvedValueOnce(jsonResponse(mockConfig));

      const result = await client.getConfig();

      expect(result).toMatchObject(mockConfig);
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should normalize direct agent /config payload shape', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.onrender.com',
        origin: 'https://vecinita-frontend.onrender.com',
        protocol: 'https:',
      } as Location);

      const renderClient = new AgentServiceClient('https://vecinita-agent.onrender.com/api/v1');

      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse({
          providers: [{ key: 'ollama', label: 'Ollama (Local)', default: true }],
          models: { ollama: ['gemma3'] },
          defaultProvider: 'ollama',
          defaultModel: 'gemma3',
        })
      );

      const result = await renderClient.getConfig();

      expect(result.providers[0]?.name).toBe('ollama');
      expect(result.providers[0]?.models).toEqual(['gemma3']);
      expect(result.defaultProvider).toBe('ollama');
      expect(result.defaultModel).toBe('gemma3');

      locationSpy.mockRestore();
    });

    it('should fail fast with clear error when config endpoint returns HTML', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response('<!doctype html><html><body>fallback</body></html>', {
          status: 200,
          headers: { 'content-type': 'text/html; charset=utf-8' },
        })
      );

      await expect(client.getConfig()).rejects.toMatchObject({
        code: 'INVALID_RESPONSE_FORMAT',
      });
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should fallback to current-origin gateway config when localhost target is unreachable', async () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        hostname: 'vecinita-frontend.example.com',
        origin: 'https://vecinita-frontend.example.com',
        protocol: 'https:',
      } as Location);

      const prodClient = new AgentServiceClient('http://localhost:8004/api/v1');
      const mockConfig: AgentConfig = {
        providers: [{ name: 'ollama', models: ['gemma3'], default: true }],
        models: { ollama: ['gemma3'] },
      };

      vi.mocked(fetch)
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockResolvedValueOnce(jsonResponse(mockConfig));

      const result = await prodClient.getConfig();

      expect(result).toMatchObject(mockConfig);
      expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
        'http://vecinita-frontend.example.com:8004/api/v1/ask/config'
      );
      expect(String(fetchMock.mock.calls[6]?.[0])).toBe(
        'https://vecinita-frontend.example.com/api/v1/ask/config'
      );

      locationSpy.mockRestore();
    });
  });

  describe('healthCheck', () => {
    it('should return true when service is healthy', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 200 }));

      const result = await client.healthCheck();

      expect(result).toBe(true);
    });

    it('should return false when service is unhealthy', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Connection failed'));

      const result = await client.healthCheck();

      expect(result).toBe(false);
    });
  });
});

describe('AgentServiceError', () => {
  it('should create error with message', () => {
    const error = new AgentServiceError('Test error');

    expect(error.message).toBe('Test error');
    expect(error.name).toBe('AgentServiceError');
  });

  it('should include status code', () => {
    const error = new AgentServiceError('Test error', 404);

    expect(error.statusCode).toBe(404);
  });

  it('should include error code', () => {
    const error = new AgentServiceError('Test error', 500, 'INTERNAL_ERROR');

    expect(error.code).toBe('INTERNAL_ERROR');
  });
});

describe('resolveAgentServiceTimeouts', () => {
  it('should use sane defaults when env values are missing or invalid', () => {
    expect(resolveAgentServiceTimeouts({})).toEqual({
      requestMs: 90000,
      streamMs: 120000,
      firstEventMs: 15000,
    });

    expect(
      resolveAgentServiceTimeouts({
        VITE_AGENT_REQUEST_TIMEOUT_MS: 'invalid',
        VITE_AGENT_STREAM_TIMEOUT_MS: '-5',
        VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS: '0',
      })
    ).toEqual({
      requestMs: 90000,
      streamMs: 120000,
      firstEventMs: 15000,
    });
  });

  it('should respect explicit timeout env values', () => {
    expect(
      resolveAgentServiceTimeouts({
        VITE_AGENT_REQUEST_TIMEOUT_MS: '95000',
        VITE_AGENT_STREAM_TIMEOUT_MS: '130000',
        VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS: '20000',
      })
    ).toEqual({
      requestMs: 95000,
      streamMs: 130000,
      firstEventMs: 20000,
    });
  });
});

describe('singleton instance', () => {
  it('should export a singleton instance', () => {
    expect(agentService).toBeInstanceOf(AgentServiceClient);
  });
});

describe('User Story 1: VITE_GATEWAY_URL-style defaults', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('uses relative /api base when VITE_GATEWAY_URL is /api (dev proxy path)', async () => {
    vi.stubEnv('VITE_GATEWAY_URL', '/api');
    vi.stubEnv('VITE_BACKEND_URL', '');
    vi.resetModules();

    const { AgentServiceClient: Client } = await import('../agentService');
    const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      hostname: 'localhost',
      origin: 'http://localhost:5173',
      protocol: 'http:',
    } as Location);

    fetchMock.mockClear();
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

    const client = new Client();
    await client.ask({ question: 'env-proxy' });

    const askUrl = fetchMock.mock.calls.map((c) => String(c[0])).find((u) => u.includes('/ask'));
    expect(askUrl).toBeDefined();
    expect(askUrl).toContain('/api/ask');
    expect(askUrl).toContain('question=env-proxy');

    locationSpy.mockRestore();
  });

  it('uses absolute gateway base when VITE_GATEWAY_URL is an http URL', async () => {
    vi.stubEnv('VITE_GATEWAY_URL', 'http://127.0.0.1:8004/api/v1');
    vi.stubEnv('VITE_BACKEND_URL', '');
    vi.resetModules();

    const { AgentServiceClient: Client } = await import('../agentService');
    const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      hostname: 'localhost',
      origin: 'http://localhost:5173',
      protocol: 'http:',
    } as Location);

    fetchMock.mockClear();
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ answer: 'ok', sources: [] }));

    const client = new Client();
    await client.ask({ question: 'env-absolute' });

    const askUrl = fetchMock.mock.calls.map((c) => String(c[0])).find((u) => u.includes('/ask'));
    expect(askUrl).toBeDefined();
    expect(askUrl).toContain('http://127.0.0.1:8004/api/v1/ask');
    expect(askUrl).toContain('question=env-absolute');

    locationSpy.mockRestore();
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { resolveApiBase } from '../../src/app/lib/apiBaseResolution';
import { resolveGatewayUrl } from '../../src/app/lib/agentApiResolution';
import { AgentServiceClient } from '../../src/app/services/agentService';

describe('Gateway integration contract: frontend URL resolution + /api/v1 routes', () => {
  const originalWindowLocation = window.location;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: originalWindowLocation,
    });
  });

  it('resolves stale/non-gateway Render URLs to the gateway /api/v1 base', () => {
    const resolved = resolveApiBase(
      'https://vecinita-agent.onrender.com',
      { hostname: 'vecinita-frontend.onrender.com', protocol: 'https:' },
      'https://vecinita-gateway.onrender.com'
    );

    expect(resolved).toBe('https://vecinita-gateway.onrender.com/api/v1');
  });

  it('rewrites stale localhost gateway ports to current browser host', () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: { hostname: '34.170.200.11', protocol: 'http:' } as Location,
    });

    const resolved = resolveGatewayUrl('http://localhost:8004/api/v1');
    expect(resolved).toBe('http://34.170.200.11:8004/api/v1');
  });

  it('builds ask-stream requests under the normalized gateway /api/v1 prefix', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: { hostname: 'localhost', protocol: 'http:' } as Location,
    });

    class ContractEventSource {
      static latest: ContractEventSource | null = null;
      readonly url: string;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;

      constructor(url: string) {
        this.url = url;
        ContractEventSource.latest = this;
      }

      close() {
        // no-op for contract test
      }
    }

    vi.stubGlobal('EventSource', ContractEventSource);

    const client = new AgentServiceClient('http://localhost:8004/api/v1');
    const streamPromise = client.askStream({ question: 'contract stream question' }, () => {});
    const stream = ContractEventSource.latest;
    expect(stream).not.toBeNull();
    expect(stream?.url).toContain('/api/v1/ask/stream?question=contract+stream+question');

    stream?.onmessage?.({
      data: JSON.stringify({ type: 'complete', answer: 'ok' }),
    } as MessageEvent);

    await expect(streamPromise).resolves.toBeUndefined();
  });
});

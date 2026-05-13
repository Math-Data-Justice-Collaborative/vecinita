import { afterEach, describe, expect, it, vi } from 'vitest';

import { resolveGatewayUrl } from '../agentApiResolution';

describe('resolveGatewayUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('does not rewrite ephemeral loopback Pact mock when page host is non-local', () => {
    vi.stubGlobal('window', {
      location: {
        hostname: 'preview.example.com',
        protocol: 'https:',
      },
    });

    const mockBase = 'http://127.0.0.1:49821/api/v1';
    expect(resolveGatewayUrl(mockBase)).toBe(mockBase);
  });

  it('still rewrites known gateway dev ports to current host when host differs', () => {
    vi.stubGlobal('window', {
      location: {
        hostname: '34.55.88.67',
        protocol: 'http:',
      },
    });

    expect(resolveGatewayUrl('http://localhost:18004/api/v1')).toBe(
      'http://34.55.88.67:18004/api/v1'
    );
  });
});

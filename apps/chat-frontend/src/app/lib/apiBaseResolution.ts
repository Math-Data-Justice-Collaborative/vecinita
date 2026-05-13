/**
 * Resolve the public **gateway** API base for the main SPA (FR-002 / SC-002).
 *
 * Render: rewrites mistaken **-agent** hostnames to **-gateway** and normalizes
 * ``/api`` → ``/api/v1``. Local dev returns configured URLs unchanged.
 * For bundle hygiene (no ``*.modal.run`` in ``VITE_*``), see ``frontendViteEnvGuards.ts``.
 */

export function resolveApiBase(
  rawUrl: string,
  locationOverride?: { hostname: string; protocol: string },
  fallbackUrl?: string
): string {
  const trimmedUrl = (rawUrl || '').trim().replace(/\/+$/, '');
  const trimmedFallbackUrl = (fallbackUrl || '').trim().replace(/\/+$/, '');

  if (typeof window === 'undefined' && !locationOverride) {
    return trimmedUrl || rawUrl;
  }

  const runtimeLocation = locationOverride ?? window.location;
  const currentHost = runtimeLocation.hostname;
  const isCurrentHostLocal =
    currentHost === 'localhost' || currentHost === '127.0.0.1' || currentHost === '::1';
  const inferredGatewayHost =
    currentHost.endsWith('.onrender.com') && currentHost.includes('-frontend')
      ? currentHost.replace('-frontend', '-gateway')
      : currentHost;

  if (isCurrentHostLocal) {
    return trimmedUrl || rawUrl;
  }

  const normalizeAbsoluteGatewayUrl = (candidateUrl: string): string | null => {
    if (!candidateUrl || !/^https?:\/\//i.test(candidateUrl)) {
      return null;
    }

    try {
      const parsed = new URL(candidateUrl);
      const isRenderHost = parsed.hostname.endsWith('.onrender.com');
      const isRenderAgentHost = isRenderHost && parsed.hostname.includes('-agent');
      const isRenderGatewayHost = isRenderHost && parsed.hostname.includes('-gateway');

      const normalizeGatewayPath = () => {
        const path = parsed.pathname.replace(/\/+$/, '');
        if (!path || path === '/' || path === '/api') {
          parsed.pathname = '/api/v1';
        }
      };

      if (isRenderAgentHost) {
        parsed.hostname = parsed.hostname.replace('-agent', '-gateway');
        parsed.protocol = 'https:';
        parsed.port = '';
        normalizeGatewayPath();
        return parsed.toString().replace(/\/+$/, '');
      }

      if (isRenderGatewayHost) {
        parsed.protocol = 'https:';
        parsed.port = '';
        normalizeGatewayPath();
        return parsed.toString().replace(/\/+$/, '');
      }
    } catch {
      return null;
    }

    return null;
  };

  if (trimmedUrl.startsWith('/')) {
    const normalizedFallbackGateway = normalizeAbsoluteGatewayUrl(trimmedFallbackUrl);
    if (normalizedFallbackGateway) {
      return normalizedFallbackGateway;
    }

    if (inferredGatewayHost !== currentHost) {
      return `${runtimeLocation.protocol}//${inferredGatewayHost}${trimmedUrl}`;
    }
    return trimmedUrl;
  }

  try {
    const parsed = new URL(trimmedUrl || rawUrl);
    const isRenderHost = parsed.hostname.endsWith('.onrender.com');
    const isRenderAgentHost = isRenderHost && parsed.hostname.includes('-agent');
    const isRenderGatewayHost = isRenderHost && parsed.hostname.includes('-gateway');
    const isConfiguredLocal =
      parsed.hostname === 'localhost' ||
      parsed.hostname === '127.0.0.1' ||
      parsed.hostname === '::1';
    const isGatewayPort = parsed.port === '8004' || parsed.port === '18004';
    const isStaleAbsoluteHost = parsed.hostname !== currentHost;

    const normalizeGatewayPath = () => {
      const path = parsed.pathname.replace(/\/+$/, '');
      if (!path || path === '/' || path === '/api') {
        parsed.pathname = '/api/v1';
      }
    };

    if (isRenderAgentHost) {
      parsed.hostname = parsed.hostname.replace('-agent', '-gateway');
      parsed.protocol = 'https:';
      parsed.port = '';
      normalizeGatewayPath();
      return parsed.toString().replace(/\/+$/, '');
    }

    if (isRenderGatewayHost) {
      parsed.protocol = 'https:';
      parsed.port = '';
      normalizeGatewayPath();
      return parsed.toString().replace(/\/+$/, '');
    }

    const isModalRunHost = parsed.hostname.endsWith('.modal.run');
    if (
      isModalRunHost &&
      inferredGatewayHost.endsWith('.onrender.com') &&
      inferredGatewayHost.includes('-gateway')
    ) {
      parsed.hostname = inferredGatewayHost;
      parsed.protocol = 'https:';
      parsed.port = '';
      normalizeGatewayPath();
      return parsed.toString().replace(/\/+$/, '');
    }

    if (isConfiguredLocal || (isGatewayPort && isStaleAbsoluteHost)) {
      parsed.hostname = inferredGatewayHost;
      if (inferredGatewayHost.endsWith('.onrender.com')) {
        parsed.protocol = 'https:';
        parsed.port = '';
      }
      return parsed.toString().replace(/\/+$/, '');
    }
  } catch {
    return trimmedUrl || rawUrl;
  }

  return trimmedUrl || rawUrl;
}

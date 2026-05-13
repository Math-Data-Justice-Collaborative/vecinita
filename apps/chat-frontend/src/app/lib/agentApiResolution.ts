export function isDirectRenderAgentHost(hostname: string): boolean {
  return hostname.endsWith('.onrender.com') && hostname.includes('-agent');
}

function isRenderFrontendHost(hostname: string): boolean {
  return hostname.endsWith('.onrender.com') && hostname.includes('-frontend');
}

function getPreferredRenderAgentBaseUrl(
  currentHost: string,
  protocol: string,
  configuredBackendUrl: string
): string | null {
  if (/^https?:\/\//i.test(configuredBackendUrl)) {
    try {
      const parsed = new URL(configuredBackendUrl);
      if (isDirectRenderAgentHost(parsed.hostname)) {
        return configuredBackendUrl;
      }
    } catch {
      // Ignore malformed overrides and fall back to hostname inference.
    }
  }

  if (!isRenderFrontendHost(currentHost)) {
    return null;
  }

  return `${protocol}//${currentHost.replace('-frontend', '-agent')}`;
}

export function stripGatewayPrefixForDirectAgent(pathname: string): string {
  const normalizedPath = pathname.replace(/\/+$/, '');
  if (normalizedPath === '/api' || normalizedPath === '/api/v1') {
    return '';
  }
  return normalizedPath;
}

export function resolveGatewayUrl(rawUrl: string, configuredBackendUrl = ''): string {
  if (typeof window === 'undefined') {
    return rawUrl;
  }

  const trimmedUrl = (rawUrl || '').trim();
  const currentHost = window.location.hostname;
  const preferredRenderAgentBaseUrl = getPreferredRenderAgentBaseUrl(
    currentHost,
    window.location.protocol,
    configuredBackendUrl
  );
  const isCurrentHostLocal =
    currentHost === 'localhost' || currentHost === '127.0.0.1' || currentHost === '::1';

  if (!isCurrentHostLocal && trimmedUrl.startsWith('/')) {
    if (preferredRenderAgentBaseUrl) {
      return preferredRenderAgentBaseUrl;
    }
    return trimmedUrl;
  }

  if (isCurrentHostLocal) {
    return trimmedUrl;
  }

  try {
    const parsed = new URL(trimmedUrl);
    const isRenderGatewayHost =
      parsed.hostname.endsWith('.onrender.com') && parsed.hostname.includes('-gateway');
    const isGatewayPort = parsed.port === '8004' || parsed.port === '18004';
    const isStaleAbsoluteHost = parsed.hostname !== currentHost;

    if (preferredRenderAgentBaseUrl && isRenderGatewayHost && isStaleAbsoluteHost) {
      return preferredRenderAgentBaseUrl;
    }

    // Only rewrite loopback/stale gateway *origin* for known gateway dev ports.
    // Arbitrary loopback URLs (e.g. Pact mock `http://127.0.0.1:<ephemeral>/api/v1`)
    // must keep their hostname so the browser reaches the mock server.
    if (isGatewayPort && isStaleAbsoluteHost) {
      parsed.hostname = currentHost;
      return parsed.toString();
    }
  } catch {
    return trimmedUrl;
  }

  return trimmedUrl;
}

export function normalizeAgentApiBaseUrl(baseUrl: string): string {
  const normalizedInput = (baseUrl || '').trim().replace(/\/+$/, '');
  if (!normalizedInput) {
    return '/api';
  }

  const ensureApiPrefix = (pathname: string): string => {
    const sanitizedPath = pathname.replace(/\/+$/, '');

    if (!sanitizedPath || sanitizedPath === '/') {
      return '/api/v1';
    }

    if (sanitizedPath === '/api') {
      return '/api/v1';
    }

    return sanitizedPath;
  };

  if (/^https?:\/\//i.test(normalizedInput)) {
    try {
      const parsed = new URL(normalizedInput);
      if (isDirectRenderAgentHost(parsed.hostname)) {
        parsed.pathname = stripGatewayPrefixForDirectAgent(parsed.pathname);
      } else {
        parsed.pathname = ensureApiPrefix(parsed.pathname);
      }
      return `${parsed.origin}${parsed.pathname}`;
    } catch {
      return normalizedInput;
    }
  }

  return normalizedInput;
}

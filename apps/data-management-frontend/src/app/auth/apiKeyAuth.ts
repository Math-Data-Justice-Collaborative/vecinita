import { browserDmHttpApiBase } from '../api/scraper-config';

const STORAGE_KEY = 'vecinita.api-key-session';

export interface ApiKeySession {
  token: string;
  preview: string;
  createdAt: string;
}

export interface ApiKeyUser {
  id: string;
  email: null;
  displayName: string;
}

function getStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.localStorage;
}

export function previewApiKey(token: string): string {
  const trimmed = token.trim();

  if (trimmed.length <= 8) {
    return trimmed;
  }

  return `${trimmed.slice(0, 4)}...${trimmed.slice(-4)}`;
}

/**
 * Reject keys that cannot be sent as `Authorization: Bearer <token>` (single
 * whitespace-delimited field) or that break SCRAPER_API_KEYS comma-separated env parsing.
 * Aligns with backend `iter_scraper_api_key_segment_errors` / scraper AuthConfig.validate.
 */
export function scraperApiKeyDmCompatibilityError(token: string): string | null {
  const trimmed = token.trim();
  if (!trimmed) {
    return 'API key is empty.';
  }
  if (/\s/.test(trimmed)) {
    return 'API key must not contain whitespace (Bearer header and SCRAPER_API_KEYS list).';
  }
  if (trimmed.includes(',')) {
    return 'API key must not contain commas; paste one key at a time or split SCRAPER_API_KEYS in server env only.';
  }
  for (let i = 0; i < trimmed.length; i += 1) {
    if (trimmed.charCodeAt(i) < 32) {
      return 'API key must not contain control characters.';
    }
  }
  return null;
}

function isApiKeySession(value: unknown): value is ApiKeySession {
  return Boolean(
    value &&
      typeof value === 'object' &&
      typeof (value as ApiKeySession).token === 'string' &&
      (value as ApiKeySession).token.trim().length > 0 &&
      typeof (value as ApiKeySession).preview === 'string' &&
      typeof (value as ApiKeySession).createdAt === 'string',
  );
}

export function buildApiKeyUser(session: ApiKeySession): ApiKeyUser {
  return {
    id: `api-key:${session.preview}`,
    email: null,
    displayName: `API key ${session.preview}`,
  };
}

export function readStoredApiKeySession(): ApiKeySession | null {
  const storage = getStorage();

  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsedValue = JSON.parse(rawValue) as unknown;
    if (!isApiKeySession(parsedValue)) {
      storage.removeItem(STORAGE_KEY);
      return null;
    }

    return parsedValue;
  } catch {
    storage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function storeApiKeySession(token: string): ApiKeySession {
  const compat = scraperApiKeyDmCompatibilityError(token);
  if (compat) {
    throw new Error(compat);
  }
  const nextSession: ApiKeySession = {
    token: token.trim(),
    preview: previewApiKey(token),
    createdAt: new Date().toISOString(),
  };

  const storage = getStorage();
  storage?.setItem(STORAGE_KEY, JSON.stringify(nextSession));

  return nextSession;
}

export function clearStoredApiKeySession(): void {
  const storage = getStorage();
  storage?.removeItem(STORAGE_KEY);
}

export function getCurrentAuthToken(): string | null {
  return readStoredApiKeySession()?.token ?? null;
}

function buildProbeUrl(): string | null {
  const baseUrl = browserDmHttpApiBase();
  if (!baseUrl) {
    return null;
  }

  return `${baseUrl}/jobs?limit=1`;
}

export async function validateApiKey(token: string): Promise<void> {
  const trimmedToken = token.trim();

  if (!trimmedToken) {
    throw new Error('API key is required.');
  }
  const compat = scraperApiKeyDmCompatibilityError(trimmedToken);
  if (compat) {
    throw new Error(compat);
  }

  const probeUrl = buildProbeUrl();
  if (!probeUrl) {
    return;
  }

  const response = await fetch(probeUrl, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${trimmedToken}`,
    },
  });

  if (response.status === 401 || response.status === 403) {
    const payload = await response.json().catch(() => null);
    const detail =
      typeof payload?.detail === 'string'
        ? payload.detail
        : typeof payload?.error === 'string'
          ? payload.error
          : '';
    const suffix = detail ? ` ${detail}` : '';
    throw new Error(`API key was rejected by the backend.${suffix}`);
  }

  if (response.status >= 400 && response.status < 500) {
    const payload = await response.json().catch(() => null);
    const message =
      typeof payload?.message === 'string'
        ? payload.message
        : typeof payload?.detail === 'string'
          ? payload.detail
          : 'API key validation failed.';
    throw new Error(message);
  }

  if (response.status >= 500) {
    throw new Error('Backend is unavailable. Retry after the service warms up.');
  }
}
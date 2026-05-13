type EnvMap = Record<string, string | undefined>;

const viteEnv = ((import.meta as ImportMeta & { env?: EnvMap }).env ?? {}) as EnvMap;
const processEnv = ((globalThis as typeof globalThis & { process?: { env?: EnvMap } }).process?.env ?? {}) as EnvMap;
const runtimeEnv = ((globalThis as typeof globalThis & { __VECINITA_ENV__?: EnvMap }).__VECINITA_ENV__ ?? {}) as EnvMap;
const LOCALHOST_NAMES = new Set(['localhost', '127.0.0.1', '0.0.0.0']);

function readEnv(...keys: string[]): string {
  for (const key of keys) {
    const value = runtimeEnv[key] ?? viteEnv[key] ?? processEnv[key];
    if (typeof value === 'string' && value.trim().length > 0) {
      return value.trim();
    }
  }

  return '';
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

function inferLocalDevApiBaseUrl(): string {
  if (typeof window === 'undefined') {
    return '';
  }

  const { hostname } = window.location;
  if (!LOCALHOST_NAMES.has(hostname)) {
    return '';
  }

  return 'http://localhost:8005';
}

/** HTTP origin of the **data-management API** (scraper-compatible `/jobs` + `/health` live here). */
const configuredDmApiBaseUrl = stripTrailingSlash(
  readEnv(
    'VITE_DM_API_BASE_URL',
    'VITE_SCRAPER_API_URL',
    'REACT_APP_RAG_API_URL',
  ) || inferLocalDevApiBaseUrl(),
);

function isHttpUrl(value: string): boolean {
  if (!value) {
    return false;
  }

  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function isDirectModalWebHost(url: string): boolean {
  try {
    return new URL(url).hostname.toLowerCase().endsWith('modal.run');
  } catch {
    return false;
  }
}

/**
 * HTTP(S) origin for browser calls to the data-management API.
 *
 * Returns empty when unset, non-http(s), or when the configured base is a direct
 * ``*.modal.run`` host (SC-001 / SC-005: use the DM API gateway origin, not Modal web URLs).
 */
export function browserDmHttpApiBase(): string {
  if (!configuredDmApiBaseUrl) {
    return '';
  }
  if (!isHttpUrl(configuredDmApiBaseUrl)) {
    return '';
  }
  if (isDirectModalWebHost(configuredDmApiBaseUrl)) {
    return '';
  }
  return configuredDmApiBaseUrl;
}

function forbiddenModalSecretsInViteEnv(): string[] {
  const hits: string[] = [];
  const keys = new Set<string>([
    ...Object.keys(viteEnv),
    ...Object.keys(processEnv),
    ...Object.keys(runtimeEnv),
  ]);
  for (const key of keys) {
    if (!key.startsWith('VITE_')) {
      continue;
    }
    if (key.toUpperCase().includes('MODAL_TOKEN')) {
      hits.push(key);
    }
  }
  return hits;
}

/** Base URL for scrape job CRUD on the **data-management API** (`/jobs` prefix). */
export function scraperJobsApiRoot(): string {
  const base = browserDmHttpApiBase();
  if (!base) {
    return '';
  }
  return `${base}/jobs`;
}

export const scraperRuntimeConfig = {
  apiBaseUrl: configuredDmApiBaseUrl,
  defaultUserId: readEnv('VITE_DEFAULT_SCRAPER_USER_ID', 'VITE_SCRAPER_USER_ID') || 'frontend-user',
};

export interface ScraperConfigDiagnostic {
  configured: boolean;
  validUrl: boolean;
  hasDeprecatedBrowserAuthEnv: boolean;
  hasDirectModalWebApiBase: boolean;
  hasModalTokenViteKeys: boolean;
  apiBaseUrl: string;
  issues: string[];
  warnings: string[];
}

export function getScraperConfigDiagnostic(): ScraperConfigDiagnostic {
  const configured = scraperRuntimeConfig.apiBaseUrl.length > 0;
  const validUrl = isHttpUrl(scraperRuntimeConfig.apiBaseUrl);
  const hasDeprecatedBrowserAuthEnv = Boolean(
    readEnv('VITE_MODAL_AUTH_KEY', 'MODAL_AUTH_KEY') &&
    readEnv('VITE_MODAL_AUTH_SECRET', 'MODAL_AUTH_SECRET'),
  );
  const hasDirectModalWebApiBase =
    configured && validUrl && isDirectModalWebHost(scraperRuntimeConfig.apiBaseUrl);
  const modalTokenKeys = forbiddenModalSecretsInViteEnv();
  const hasModalTokenViteKeys = modalTokenKeys.length > 0;

  const issues: string[] = [];
  const warnings: string[] = [];

  if (!configured) {
    issues.push('Missing VITE_DM_API_BASE_URL (HTTP origin of the data-management API)');
  }

  if (configured && !validUrl) {
    issues.push('Data-management API base URL must be a valid http(s) URL');
  }

  if (hasDirectModalWebApiBase) {
    issues.push(
      'Data-management API base URL must not point at a *.modal.run host; use the DM API HTTP origin (SC-001 / SC-005).',
    );
  }

  if (hasModalTokenViteKeys) {
    issues.push(
      `Remove Modal token keys from the browser bundle: ${modalTokenKeys.join(', ')} (SC-005).`,
    );
  }

  if (hasDeprecatedBrowserAuthEnv) {
    warnings.push('Browser Modal auth env vars are ignored; configure Modal credentials on the data-management API only.');
  }

  return {
    configured,
    validUrl,
    hasDeprecatedBrowserAuthEnv,
    hasDirectModalWebApiBase,
    hasModalTokenViteKeys,
    apiBaseUrl: scraperRuntimeConfig.apiBaseUrl,
    issues,
    warnings,
  };
}

export function getScraperHealthUrl(): string | null {
  const base = browserDmHttpApiBase();
  if (!base) {
    return null;
  }

  return `${base}/health`;
}

export function isScraperConfigured(): boolean {
  return browserDmHttpApiBase().length > 0;
}
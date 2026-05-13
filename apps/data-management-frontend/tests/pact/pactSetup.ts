import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const DM_API_PACT_CONSUMER = 'dm-frontend';

/** Scraper-compatible HTTP surface mounted on the data-management API. */
export const DM_SCRAPER_API_PROVIDER = 'vecinita-data-management-api';

export function resolveDmPactOutputDir(): string {
  return path.resolve(__dirname, '../../pacts');
}

export function resolveDmPactLogLevel(): 'error' | 'warn' | 'info' {
  return process.env.PACT_LOG_LEVEL === 'info' ? 'info' : 'error';
}

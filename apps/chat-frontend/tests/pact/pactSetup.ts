import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Consumer name aligned with TESTING_DOCUMENTATION / two-consumer plan */
export const CHAT_GATEWAY_PACT_CONSUMER = 'chat-frontend';

/** Gateway provider surface for chat agent routes under `/api/v1` */
export const CHAT_GATEWAY_PACT_PROVIDER = 'vecinita-gateway';

/** Directory for generated pact JSON (gitignored); CI can publish as an artifact */
export function resolveChatPactOutputDir(): string {
  return path.resolve(__dirname, '../../pacts');
}

export function resolveChatPactLogLevel(): 'error' | 'warn' | 'info' {
  return process.env.PACT_LOG_LEVEL === 'info' ? 'info' : 'error';
}

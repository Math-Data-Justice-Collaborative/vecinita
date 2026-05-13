/**
 * Map HTTP / network failures from the data-management API into **operator-safe**
 * messages (no raw internal hostnames, stack traces, or Modal diagnostics in UI text).
 *
 * Feature 007 / spec edge cases: embedding or model path unavailable, scraper throttling,
 * Modal cold start — callers should surface these strings to operators instead of upstream dumps.
 */

const INTERNAL_HOST_PATTERNS = [
  /\bdpg-[a-z0-9-]+\b/gi,
  /\b[a-z0-9.-]+\.internal\b/gi,
  /\b0\.0\.0\.0:\d+\b/g,
];

function truncateForUi(text: string, max = 220): string {
  const t = text.trim();
  if (t.length <= max) {
    return t;
  }
  return `${t.slice(0, max - 1)}…`;
}

/** Remove common infra leaks from backend error strings. */
export function sanitizeOperatorErrorMessage(raw: string): string {
  let s = raw.replace(/\s+/g, ' ').trim();
  for (const re of INTERNAL_HOST_PATTERNS) {
    s = s.replace(re, '[internal host]');
  }
  if (/traceback|file "|line \d+/i.test(s)) {
    return 'An internal error occurred; see server logs for details.';
  }
  return truncateForUi(s);
}

function pickDetailFromBody(body: unknown): string | undefined {
  if (!body || typeof body !== 'object') {
    return undefined;
  }
  const rec = body as Record<string, unknown>;
  const detail = rec.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((entry) => {
        if (entry && typeof entry === 'object' && 'msg' in (entry as object)) {
          return String((entry as { msg?: unknown }).msg ?? '');
        }
        return typeof entry === 'string' ? entry : JSON.stringify(entry);
      })
      .filter(Boolean);
    if (parts.length) {
      return parts.join('; ');
    }
  }
  const msg = rec.message;
  if (typeof msg === 'string' && msg.trim()) {
    return msg.trim();
  }
  return undefined;
}

/** Stable, human-readable copy for HTTP status codes from the DM / scraper API. */
export function operatorMessageForHttpStatus(status: number): string {
  if (status === 429) {
    return 'The service is busy (rate limited). Please wait a moment and try again.';
  }
  if (status === 408 || status === 504) {
    return 'The request timed out. If Modal or workers were cold-starting, retry in a few seconds.';
  }
  if (status === 503) {
    return 'A dependency is temporarily unavailable. Please retry shortly.';
  }
  if (status === 502) {
    return 'The data-management service could not complete the request with an upstream worker. Please retry or check worker health.';
  }
  if (status >= 500) {
    return 'The data-management service hit an unexpected error. Please retry or contact an operator.';
  }
  if (status === 401 || status === 403) {
    return 'You are not authorized for this action. Check your API key or sign in again.';
  }
  if (status === 404) {
    return 'The requested resource was not found.';
  }
  if (status === 409) {
    return 'This action conflicts with the current state (for example, a job already finished).';
  }
  return `The request could not be completed (HTTP ${status}).`;
}

/** Prefer backend detail when safe; otherwise fall back to status-based guidance. */
export function normalizeUpstreamErrorMessage(status: number, body: unknown): string {
  const detail = pickDetailFromBody(body);
  if (detail) {
    return sanitizeOperatorErrorMessage(detail);
  }
  return operatorMessageForHttpStatus(status);
}

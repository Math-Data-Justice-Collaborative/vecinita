import { describe, expect, it } from 'vitest';

import {
  normalizeUpstreamErrorMessage,
  operatorMessageForHttpStatus,
  sanitizeOperatorErrorMessage,
} from './operatorUpstreamErrors';

describe('sanitizeOperatorErrorMessage', () => {
  it('replaces dpg-* and *.internal host patterns', () => {
    const raw = 'connect dpg-abc123 failed at db.internal:5432';
    expect(sanitizeOperatorErrorMessage(raw)).toContain('[internal host]');
    expect(sanitizeOperatorErrorMessage(raw)).not.toMatch(/dpg-abc123/i);
    expect(sanitizeOperatorErrorMessage(raw)).not.toMatch(/\.internal/i);
  });

  it('replaces traceback-like blobs with a generic message', () => {
    const raw = 'Traceback (most recent call last):\n  File "app.py", line 1';
    expect(sanitizeOperatorErrorMessage(raw)).toBe(
      'An internal error occurred; see server logs for details.',
    );
  });

  it('truncates very long strings', () => {
    const raw = 'x'.repeat(400);
    const out = sanitizeOperatorErrorMessage(raw);
    expect(out.length).toBeLessThanOrEqual(220);
    expect(out.endsWith('…')).toBe(true);
  });
});

describe('operatorMessageForHttpStatus', () => {
  it('returns stable copy for throttling and cold-start-ish statuses', () => {
    expect(operatorMessageForHttpStatus(429)).toMatch(/rate limited/i);
    expect(operatorMessageForHttpStatus(504)).toMatch(/timed out/i);
    expect(operatorMessageForHttpStatus(503)).toMatch(/temporarily unavailable/i);
    expect(operatorMessageForHttpStatus(502)).toMatch(/upstream worker/i);
  });
});

describe('normalizeUpstreamErrorMessage', () => {
  it('prefers string detail and sanitizes it', () => {
    expect(
      normalizeUpstreamErrorMessage(500, { detail: 'Error at dpg-xyz host' }),
    ).toContain('[internal host]');
  });

  it('joins FastAPI-style detail array entries', () => {
    expect(
      normalizeUpstreamErrorMessage(422, {
        detail: [{ msg: 'field required', type: 'missing' }, { msg: 'bad type' }],
      }),
    ).toMatch(/field required.*bad type/i);
  });

  it('falls back to status message when body has no usable detail', () => {
    expect(normalizeUpstreamErrorMessage(429, {})).toMatch(/rate limited/i);
    expect(normalizeUpstreamErrorMessage(418, {})).toMatch(/HTTP 418/);
  });
});

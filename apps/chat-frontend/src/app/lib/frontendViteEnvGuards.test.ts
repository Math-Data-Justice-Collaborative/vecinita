import { describe, expect, it } from 'vitest';

import { collectForbiddenViteEnvIssues } from './frontendViteEnvGuards';

describe('frontendViteEnvGuards (SC-005)', () => {
  it('allows gateway and localhost URLs', () => {
    expect(
      collectForbiddenViteEnvIssues({
        VITE_GATEWAY_URL: 'http://localhost:8004/api/v1',
      })
    ).toEqual([]);
  });

  it('rejects modal.run in VITE values', () => {
    const issues = collectForbiddenViteEnvIssues({
      VITE_GATEWAY_URL: 'https://vecinita--app.modal.run',
    });
    expect(issues.length).toBeGreaterThan(0);
    expect(issues[0]).toContain('modal.run');
  });

  it('rejects VITE_* keys containing MODAL_TOKEN', () => {
    const issues = collectForbiddenViteEnvIssues({
      VITE_GATEWAY_URL: 'http://localhost:8004/api/v1',
      VITE_MODAL_TOKEN_SECRET: 'x',
    });
    expect(issues.some((i) => i.includes('MODAL_TOKEN'))).toBe(true);
  });
});

import { test, expect } from '@playwright/test';

test.describe('Spanish ask retrieval intent', () => {
  test('doctor-intent Spanish query avoids school-only context drift', async ({ page }) => {
    const response = await page.request.get('http://127.0.0.1:18004/api/v1/ask', {
      params: {
        question: 'Dame unos doctos en Providence',
        lang: 'es',
      },
      timeout: 120000,
    });

    expect(response.status()).toBe(200);
    const payload = await response.json();

    expect(payload).toHaveProperty('answer');
    expect(typeof payload.answer).toBe('string');

    const answerLower = (payload.answer || '').toLowerCase();
    const indicatesSchoolOnly =
      answerLower.includes('providenceschools.org') ||
      (answerLower.includes('school district') && answerLower.includes('insufficient'));

    expect(indicatesSchoolOnly).toBeFalsy();
  });
});

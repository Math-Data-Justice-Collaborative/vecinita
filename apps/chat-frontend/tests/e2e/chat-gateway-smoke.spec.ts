import { expect, test, type Page } from '@playwright/test';

async function installGatewayFixtures(page: Page): Promise<void> {
  await page.route('**/ask/config**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        providers: [{ name: 'groq', models: ['llama-3.1-8b'], default: true }],
        models: { groq: ['llama-3.1-8b'] },
        defaultProvider: 'groq',
        defaultModel: 'llama-3.1-8b',
      }),
    });
  });

  await page.route('**/ask/stream**', async (route) => {
    const body = [
      `data: ${JSON.stringify({
        type: 'token',
        content: 'Smoke',
      })}\n\n`,
      `data: ${JSON.stringify({
        type: 'complete',
        answer: 'Smoke streaming reply',
        sources: [],
        thread_id: 'smoke-thread',
      })}\n\n`,
    ].join('');

    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
      body,
    });
  });
}

test.describe('chat gateway smoke (FR-009)', () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
    await context.addInitScript(() => {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch {
        // ignore
      }
    });
  });

  test('loads chat, streams a turn, exposes lang and keyboard target', async ({ page }) => {
    await installGatewayFixtures(page);
    const modalRunUrls: string[] = [];
    page.on('request', (req) => {
      const url = req.url();
      if (url.toLowerCase().includes('modal.run')) {
        modalRunUrls.push(url);
      }
    });
    await page.goto('/');

    await expect(page.locator('html')).toHaveAttribute('lang', 'en');

    const composer = page.locator('main textarea').first();
    await composer.focus();
    await expect(composer).toBeFocused();

    await composer.fill('Smoke pact question');
    await composer.press('Enter');

    await expect(page.getByText('Smoke streaming reply', { exact: false })).toBeVisible({
      timeout: 30_000,
    });

    expect(
      modalRunUrls,
      'main SPA must not call *.modal.run from the browser (SC-002/SC-005)'
    ).toEqual([]);
  });
});

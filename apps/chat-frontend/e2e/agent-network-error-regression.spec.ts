import { test, expect } from '@playwright/test';

test.describe('Agent network regressions', () => {
  test('app shell remains usable when config fetch fails with a network error', async ({
    page,
  }) => {
    await page.route(/\/api(?:\/v1)?\/ask\/config(\?.*)?$/, async (route) => {
      await route.abort('failed');
    });

    await page.goto('/');

    await expect(page.getByRole('heading', { name: /Vecinita/i })).toBeVisible();
    await expect(
      page.getByRole('textbox', { name: /Escribe tu pregunta|Type your question/i })
    ).toBeVisible();
  });

  test('shows a user-facing error when ask fails with a network error', async ({ page }) => {
    await page.route(/\/api(?:\/v1)?\/ask\/config(\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json; charset=utf-8',
        body: JSON.stringify({
          providers: [{ name: 'ollama', models: ['gemma3'], default: true }],
          models: { ollama: ['gemma3'] },
          defaultProvider: 'ollama',
          defaultModel: 'gemma3',
        }),
      });
    });

    await page.route(/\/api(?:\/v1)?\/ask\/stream(\?.*)?$/, async (route) => {
      await route.abort('failed');
    });

    await page.route(/\/api(?:\/v1)?\/ask(\?.*)?$/, async (route) => {
      await route.abort('failed');
    });

    await page.goto('/');
    const suggestionButton = page.getByRole('button', {
      name: /problemas ambientales|environmental concerns/i,
    });
    await expect(suggestionButton).toBeVisible({ timeout: 15000 });
    await suggestionButton.click();

    await expect(
      page.locator('[data-message-role="assistant"], [class*="destructive"]').filter({
        hasText: /Lo siento, encontr[eé] un error:|Sorry, I encountered an error:/i,
      })
    ).toBeVisible({ timeout: 30000 });
  });
});

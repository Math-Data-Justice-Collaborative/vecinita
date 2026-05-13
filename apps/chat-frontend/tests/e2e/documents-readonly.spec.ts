import { expect, test } from '@playwright/test';

test('documents tab exposes no write controls', async ({ page }) => {
  await page.route('**/api/v1/documents/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_chunks: 1,
        unique_sources: 1,
        filtered: false,
        avg_chunk_size: 120,
        embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
        embedding_dimension: 384,
        sources: [{ url: 'https://example.org/a', title: 'A', tags: [] }],
      }),
    });
  });
  await page.route('**/api/v1/documents/tags?limit=100', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ tags: [] }),
    });
  });

  await page.goto('/documents');
  await expect(page.getByRole('button', { name: /add/i })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /delete/i })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /edit/i })).toHaveCount(0);
});

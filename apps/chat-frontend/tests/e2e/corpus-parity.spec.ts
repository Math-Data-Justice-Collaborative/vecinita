import { expect, test } from '@playwright/test';

test('documents tab renders canonical corpus projection', async ({ page }) => {
  await page.route('**/api/v1/documents/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_chunks: 3,
        unique_sources: 1,
        filtered: false,
        avg_chunk_size: 100,
        embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
        embedding_dimension: 384,
        sources: [
          {
            id: 'doc-1',
            url: 'https://example.org/community',
            title: 'Community Resource',
            source_domain: 'example.org',
            source_of_truth: 'postgres',
            canonical_visibility_updated_at: '2026-01-01T00:00:00.000Z',
            tags: ['community'],
          },
        ],
      }),
    });
  });
  await page.route('**/api/v1/documents/tags?limit=100', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        tags: [{ tag: 'community', source_count: 1 }],
      }),
    });
  });

  await page.goto('/documents');
  await expect(page.getByText('Community Resource')).toBeVisible();
  await expect(page.getByText('https://example.org/community')).toBeVisible();
});

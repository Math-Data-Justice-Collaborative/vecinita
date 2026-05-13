import type { Page } from '@playwright/test';

interface StreamCompletePayload {
  answer: string;
  sources?: unknown[];
  thread_id?: string;
}

export async function installChatRenderingFixtures(
  page: Page,
  completePayload: StreamCompletePayload
): Promise<void> {
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
    const body = `data: ${JSON.stringify({
      type: 'complete',
      answer: completePayload.answer,
      sources: completePayload.sources ?? [],
      thread_id: completePayload.thread_id ?? 'render-thread',
    })}\n\n`;

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

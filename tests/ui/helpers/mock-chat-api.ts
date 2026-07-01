import type { Page, Route } from "@playwright/test";

const ASK_SSE =
  'data: {"token":"Local "}\n\n' +
  'data: {"token":"aid info."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

/** Mock ChatRAG backend routes used on initial shell load (UJ-001 / UJ-009). */
export async function mockChatApi(
  page: Page,
  options?: { tags?: { slug: string; label: string; language: string }[] },
): Promise<void> {
  const tags = options?.tags ?? [];

  await page.route("**/api/v1/tags", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tags: tags.map((tag) => ({
          ...tag,
          document_count: 1,
        })),
      }),
    });
  });

  await page.route("**/api/v1/warm", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/api/v1/documents**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        page: 1,
        page_size: 20,
        total: 0,
      }),
    });
  });
}

/** Mock streaming ask endpoint for ChatPanel ↔ Sidebar interaction tests. */
export async function mockChatStream(
  page: Page,
  sseBody: string = ASK_SSE,
): Promise<void> {
  await page.route("**/api/v1/ask/stream", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sseBody,
    });
  });
}

export async function mockChatShell(page: Page): Promise<void> {
  await mockChatApi(page);
  await mockChatStream(page);
}

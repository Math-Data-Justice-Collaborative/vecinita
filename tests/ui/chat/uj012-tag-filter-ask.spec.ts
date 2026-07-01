import { expect, test } from "@playwright/test";

import { mockChatApi, mockChatStream } from "../helpers/mock-chat-api";

/**
 * UJ-012: Sidebar tag chips ↔ ChatPanel ask request includes selected tags.
 */
test.describe("Tag-filtered ask", () => {
  test("selected sidebar tag is sent with the stream request", async ({
    page,
  }) => {
    await mockChatApi(page, {
      tags: [{ slug: "legal-aid", label: "Legal aid", language: "en" }],
    });
    await mockChatStream(page);

    let capturedTags: string[] | undefined;
    await page.route("**/api/v1/ask/stream", async (route) => {
      const body = route.request().postDataJSON() as { tags?: string[] };
      capturedTags = body.tags;
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          'data: {"token":"Tagged "}\n\n' +
          'data: {"token":"response."}\n\n' +
          'data: {"sources":[]}\n\n' +
          'data: {"done":true}\n\n',
      });
    });

    await page.goto("/");
    await page.getByTestId("tag-filter-chips").getByRole("button", { name: "Legal aid" }).click();
    await page.getByLabel(/your question/i).fill("Hours for legal aid?");
    await page.getByRole("button", { name: /^ask$/i }).click();

    await expect(page.getByText(/tagged response\./i)).toBeVisible();
    expect(capturedTags).toEqual(["legal-aid"]);
  });
});

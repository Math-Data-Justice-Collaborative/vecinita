import { expect, test } from "@playwright/test";

import { mockChatShell } from "../helpers/mock-chat-api";

const SSE_A =
  'data: {"token":"First "}\n\n' +
  'data: {"token":"answer."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

const SSE_B =
  'data: {"token":"Second "}\n\n' +
  'data: {"token":"answer."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

/**
 * UJ-025: Sidebar previous-chats list ↔ ChatPanel restore interaction.
 */
test.describe("Previous chats list", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
      localStorage.setItem("vecinita.locale", "en");
    });
    await mockChatShell(page);
    let askCount = 0;
    await page.route("**/api/v1/ask/stream", async (route) => {
      askCount += 1;
      const body = askCount === 1 ? SSE_A : SSE_B;
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body,
      });
    });
  });

  test("archives first chat and restores it from the sidebar list", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByLabel(/your question/i).fill("First question?");
    await page.getByRole("button", { name: /^ask$/i }).click();
    await expect(page.getByText(/first answer\./i)).toBeVisible();

    await page.getByRole("button", { name: /new chat/i }).click();

    await page.getByLabel(/your question/i).fill("Second question?");
    await page.getByRole("button", { name: /^ask$/i }).click();
    await expect(page.getByText(/second answer\./i)).toBeVisible();

    const previousToggle = page.getByRole("button", { name: /previous chats/i });
    if ((await previousToggle.getAttribute("aria-expanded")) !== "true") {
      await previousToggle.click();
    }

    await page.getByTestId("previous-chats-list").getByRole("button", { name: /first question/i }).click();

    await expect(page.getByTestId("message-list")).toContainText("First question?");
    await expect(page.getByTestId("message-list")).toContainText(/first answer\./i);
    await expect(page.getByTestId("message-list")).not.toContainText("Second question?");
  });
});

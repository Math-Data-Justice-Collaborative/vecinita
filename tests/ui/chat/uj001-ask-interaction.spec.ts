import { expect, test } from "@playwright/test";

import { mockChatShell } from "../helpers/mock-chat-api";

/**
 * UJ-001: ChatPanel input + stream response appear in the message list.
 * Exercises Sidebar shell ↔ ChatPanel coordination in a real browser.
 */
test.describe("Chat ask interaction", () => {
  test.beforeEach(async ({ page }) => {
    await mockChatShell(page);
  });

  test("streams an answer into the message list after Ask", async ({ page }) => {
    const question = "Where can I find legal aid?";
    await page.goto("/");

    await page.getByLabel(/your question/i).fill(question);
    await page.getByRole("button", { name: /^ask$/i }).click();

    await expect(page.getByTestId("message-list")).toContainText(question);
    await expect(page.getByTestId("message-list")).toContainText(
      /local aid info\./i,
    );
  });
});

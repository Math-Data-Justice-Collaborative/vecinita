import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/** UJ-009 (browser): Navigate from chat to corpus browse in a real browser. */
test.describe("Corpus browse navigation", () => {
  test.beforeEach(async ({ page }) => {
    await mockChatApi(page);
  });

  test("opens corpus list from sidebar navigation", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /^corpus$/i }).click();

    await expect(page.getByLabel(/search/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /back to chat/i })).toBeVisible();
    await expect(page.getByTestId("corpus-list")).toBeAttached();
  });
});

import { expect, test } from "@playwright/test";

import { mockChatShell } from "../helpers/mock-chat-api";

/**
 * BUG-2026-06-25 / UJ-024: conversation must survive Chat → Corpus → Chat.
 * Shell-owned state (App ↔ ChatPanel) is unmounted on corpus navigation.
 */
test.describe("Chat state across navigation", () => {
  test.beforeEach(async ({ page }) => {
    await mockChatShell(page);
    await page.addInitScript(() => {
      localStorage.clear();
      localStorage.setItem("vecinita.locale", "en");
    });
  });

  test("preserves messages after Corpus round-trip", async ({ page }) => {
    const question = "Where can I find legal aid?";
    await page.goto("/");

    await page.getByLabel(/your question/i).fill(question);
    await page.getByRole("button", { name: /^ask$/i }).click();
    await expect(page.getByText(question)).toBeVisible();
    await expect(page.getByText(/local aid info\./i)).toBeVisible();

    await page.getByRole("button", { name: /^corpus$/i }).click();
    await expect(page.getByLabel(/search title or url/i)).toBeVisible();

    await page.getByRole("button", { name: /^chat$/i }).click();
    await expect(page.getByText(question)).toBeVisible();
    await expect(page.getByText(/local aid info\./i)).toBeVisible();
    await expect(page.getByLabel(/your question/i)).toBeVisible();
  });
});

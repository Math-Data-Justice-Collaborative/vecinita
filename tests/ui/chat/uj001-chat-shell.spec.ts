import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/** UJ-001 / UJ-022 (browser): ChatRAG shell loads with sidebar and locale toggle. */
test.describe("ChatRAG shell", () => {
  test.beforeEach(async ({ page }) => {
    await mockChatApi(page);
  });

  test("renders sidebar, header, and English new-chat control", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expect(page.getByTestId("app-header")).toBeVisible();
    await expect(page.getByRole("button", { name: /new chat/i })).toBeVisible();
    await expect(page.getByTestId("language-toggle")).toBeVisible();
  });

  test("switches UI strings to Spanish via language toggle", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByTestId("language-toggle").getByRole("button", { name: "ES" }).click();
    await expect(page.getByRole("button", { name: /chat nuevo/i })).toBeVisible();
  });
});

import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/**
 * UJ-073 / TC-226: ChatRAG Feedback nav → page → submit success (F68).
 */
test.describe("UJ-073 anonymous feedback", () => {
  test("navigates to Feedback page and shows success after submit", async ({
    page,
  }) => {
    await mockChatApi(page);

    await page.route("**/api/v1/feedback", async (route) => {
      if (route.request().method() !== "POST") {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "11111111-1111-4111-8111-111111111111",
          created_at: "2026-08-04T12:00:00Z",
        }),
      });
    });

    await page.goto("/");
    await page.getByTestId("nav-feedback").click();
    await expect(page.getByTestId("feedback-page")).toBeVisible();

    await page.getByTestId("feedback-message").fill(
      "Search felt truncated on mobile.",
    );
    await page.getByTestId("feedback-submit").click();

    await expect(page.getByTestId("feedback-success")).toBeVisible();
  });
});

import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/**
 * UJ-052 / TC-160: cold-start wait shell — starting-up + fact + consent + donate.
 */
test.describe("UJ-052 cold-start wait", () => {
  test("shows wait UX and consent controls on cold-start retry", async ({
    page,
  }) => {
    await mockChatApi(page);

    let attempts = 0;
    await page.route("**/api/v1/ask/stream", async (route) => {
      attempts += 1;
      if (attempts === 1) {
        await route.abort("failed");
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          'data: {"token":"Local "}\n\n' +
          'data: {"token":"aid info."}\n\n' +
          'data: {"sources":[]}\n\n' +
          'data: {"done":true}\n\n',
      });
    });

    await page.goto("/");
    await page.getByLabel(/your question/i).fill("Where can I find legal aid?");
    await page.getByRole("button", { name: /^ask$/i }).click();

    await expect(page.getByTestId("cold-start-wait")).toBeVisible();
    await expect(page.getByTestId("cold-start-fact")).toBeVisible();
    await expect(page.getByTestId("cold-start-donate")).toHaveAttribute(
      "href",
      /wrwc\.org\/donate/,
    );
    await expect(page.getByTestId("cold-start-consent")).toBeVisible();
    await expect(
      page.getByTestId("cold-start-consent-accept"),
    ).toBeVisible();
    await expect(
      page.getByTestId("cold-start-consent-opt-out"),
    ).toBeVisible();

    await page.getByTestId("cold-start-consent-accept").click();
    await expect(page.getByTestId("cold-start-consent")).toHaveCount(0);

    await expect(page.getByTestId("message-list")).toContainText(
      /local aid info\./i,
    );
  });
});

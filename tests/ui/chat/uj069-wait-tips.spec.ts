import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/**
 * UJ-069 / TC-216–217: typed wait catalog (tip + marketing) + F40 consent/donate;
 * no survey UI.
 */
test.describe("UJ-069 wait tips + marketing", () => {
  test("rotates tip/marketing kinds; keeps consent and donate; no survey", async ({
    page,
  }) => {
    await mockChatApi(page);

    // First attempt fails → cold-start wait UX; second request stays open so
    // rotation remains visible for the rest of the test.
    let attempts = 0;
    await page.route("**/api/v1/ask/stream", async (route) => {
      attempts += 1;
      if (attempts === 1) {
        await route.abort("failed");
        return;
      }
      await new Promise<void>(() => {
        /* hold open until Playwright tears down the route */
      });
    });

    await page.clock.install();

    await page.goto("/");
    await page.getByLabel(/your question/i).fill("Where can I find legal aid?");
    await page.getByRole("button", { name: /^ask$/i }).click();

    await expect(page.getByTestId("cold-start-wait")).toBeVisible();
    const entry = page.getByTestId("cold-start-fact");
    await expect(entry).toBeVisible();
    const initialKind = await entry.getAttribute("data-kind");
    expect(["fact", "tip", "marketing"]).toContain(initialKind);

    await expect(page.getByTestId("cold-start-survey")).toHaveCount(0);
    await expect(page.getByText(/mini survey/i)).toHaveCount(0);

    await expect(page.getByTestId("cold-start-donate")).toHaveAttribute(
      "href",
      /wrwc\.org\/donate/,
    );
    await expect(page.getByTestId("cold-start-consent")).toBeVisible();
    await page.getByTestId("cold-start-consent-accept").click();
    await expect(page.getByTestId("cold-start-consent")).toHaveCount(0);

    const kinds = new Set<string>();
    for (let i = 0; i < 20; i += 1) {
      const kind = await entry.getAttribute("data-kind");
      if (kind) {
        kinds.add(kind);
      }
      if (kinds.has("tip") && kinds.has("marketing") && kinds.has("fact")) {
        break;
      }
      await page.clock.fastForward(4_500);
    }

    expect(kinds.has("tip")).toBe(true);
    expect(kinds.has("marketing")).toBe(true);
    expect(kinds.has("fact")).toBe(true);
  });
});

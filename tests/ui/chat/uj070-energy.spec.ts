import { expect, test } from "@playwright/test";

import { mockChatApi } from "../helpers/mock-chat-api";

/**
 * UJ-070 / TC-220 + TC-231: energy chip, car line, advisory after ask.
 */
test.describe("UJ-070 energy estimate", () => {
  test("shows chip, car distance, and advisory after stream completes", async ({
    page,
  }) => {
    await mockChatApi(page);

    await page.route("**/api/v1/ask/stream", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          'data: {"token":"Local "}\n\n' +
          'data: {"token":"hours posted."}\n\n' +
          'data: {"sources":[]}\n\n' +
          'data: {"done":true,"cache_hit":"none","energy_estimate":{"wh":0.02,"g_co2e":0.008,"method":"tdp_util_walltime_v1","advisory":"Approximate.","car_km_equiv":0.00003,"car_m_equiv":0.03}}\n\n',
      });
    });

    await page.goto("/");
    await page.getByLabel(/your question/i).fill("When is the food pantry open?");
    await page.getByRole("button", { name: /^ask$/i }).click();

    await expect(page.getByTestId("energy-estimate")).toBeVisible();
    await expect(page.getByTestId("energy-chip")).toContainText(/Wh/i);
    await expect(page.getByTestId("energy-car-line")).toContainText(/mi/);
    await expect(page.getByTestId("energy-advisory")).toContainText(
      /approximate/i,
    );

    await page.getByTestId("energy-use-guide-toggle").click();
    await expect(page.getByTestId("energy-use-guide")).toBeVisible();
  });
});
